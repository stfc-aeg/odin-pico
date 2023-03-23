import ctypes
import time
import numpy as np
import h5py

import logging
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from concurrent.futures import thread
from tornado.concurrent import run_on_executor
from concurrent import futures

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

from odin_pico.pico_block_device import PicoBlockDevice
from odin_pico.pico_liveview_device import PicoLiveView
from odin_pico.pico_util import PicoUtil 

class PicoController():
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self,lock,handle):
        self.live_capture_running = False

        self.handle = handle
        self.pico_block_device = PicoBlockDevice(self.handle)
        self.pico_util = PicoUtil()
        self.lock = lock

        self.streaming_buffer = []
        self.streaming_buffer.append(np.zeros(10000,dtype='int16'))
        self.test_view = PicoLiveView(self.handle,self.streaming_buffer,10000)


        self.resolution = 0
        self.timebase = 0
        self.connection_attempted = -1

        self.channel_names = ['a', 'b', 'c', 'd']
        self.channels = {}
        i = 0
        for name in self.channel_names:
            self.channels[name] = self.pico_util.set_channel_defaults(name,i)
            i += 1
    
        self.trigger = self.pico_util.set_trigger_defaults()
        self.capture = self.pico_util.set_capture_defaults()
        self.status = self.pico_util.set_status_defaults()

        adapter_status = ParameterTree ({
            'openunit': (lambda: self.status["openunit"], None),
            'pico_setup_verify': (lambda: self.status["pico_setup_verify"], None),
            'channel_setup_verify': (lambda: self.status["channel_setup_verify"], None),
            'channel_trigger_verify': (lambda: self.status["channel_trigger_verify"], None),
            'capture_settings_verify': (lambda: self.status["capture_settings_verify"], None),
        })

        pico_commands = ParameterTree ({
            'run_capture': (lambda: self.connection_attempted, self.run_capture)
        })

        self.chan_params = {}
        for channel in self.channel_names:
            self.chan_params[channel] = ParameterTree(
                {
                'channel_id': (partial(self.get_channel_value, channel, "channel_id"), None),
                'active': (partial(self.get_channel_value, channel, "active"), partial(self.set_channel_value, channel, "active")),
                'verified': (partial(self.get_channel_value, channel,"verified"), None),
                'coupling': (partial(self.get_channel_value, channel, "coupling"), partial(self.set_channel_value, channel, "coupling")),
                'range': (partial(self.get_channel_value, channel, "range"), partial(self.set_channel_value, channel, "range")),
                'offset': (partial(self.get_channel_value, channel, "offset"), partial(self.set_channel_value, channel, "offset"))
                }
            )

        pico_trigger = ParameterTree ({
            'active': (lambda: self.trigger["active"], partial(self.set_trigger_value, "active")),
            'auto_trigger': (lambda: self.trigger["auto_trigger_ms"], partial(self.set_trigger_value, "auto_trigger_ms")),
            'direction': (lambda: self.trigger["direction"], partial(self.set_trigger_value, "direction")),
            'delay': (lambda: self.trigger["delay"], partial(self.set_trigger_value, "delay")),
            'source': (lambda: self.trigger["source"], partial(self.set_trigger_value, "source")),
            'threshold': (lambda: self.trigger["threshold"], partial(self.set_trigger_value, "threshold"))
        })

        pico_capture = ParameterTree ({
            'pre_trig_samples': (lambda: self.capture["pre_trig_samples"], partial(self.set_capture_value, "pre_trig_samples")),
            'post_trig_samples': (lambda: self.capture["post_trig_samples"], partial(self.set_capture_value, "post_trig_samples")),
            'n_captures': (lambda: self.capture["n_captures"], partial(self.set_capture_value, "n_captures"))
        })

        pico_settings = ParameterTree ({
            'resolution': (lambda: self.resolution, self.set_resolution),
            'timebase': (lambda: self.timebase, self.set_timebase),
            'channels':{name: channel for (name, channel) in self.chan_params.items()},
            'trigger': pico_trigger,
            'capture': pico_capture
        })

        self.pico_param_tree = ParameterTree ({
            'status': adapter_status,
            'commands': pico_commands,
            'settings': pico_settings
        })

        self.pico_streaming_data = ParameterTree ({
            'recent_data_array' : (self.get_streaming_values, None)
        })

        self.verify_chain()

        self.test_view.initalise_parameters()
        



    def get_streaming_values(self):
        return (self.streaming_buffer[0][::10]).tolist()

    # Return function for channel parameters to avoid late binding issues
    def get_channel_value(self,channel,value):
        return self.channels[channel][value]

    # Various generic setting funtions for values
    def set_resolution(self, resolution):
        self.resolution = resolution
        self.verify_chain()

    def set_timebase(self, timebase):
        self.timebase = timebase
        self.verify_chain()

    def set_capture_value(self,key,value):
        self.capture[key] = value
        self.verify_chain()

    def set_trigger_value(self,key,value):
        if key in self.pico_block_device.trigger_dicts:
            if value in self.pico_block_device.trigger_dicts[key]:
                self.trigger[key] = value
        else:
            self.trigger[key] = value
        self.verify_chain()

    def set_channel_value(self, channel, key, value):
        if key in self.pico_block_device.channel_dicts:
            if value in self.pico_block_device.channel_dicts[key]:
                self.channels[channel][key] = value
                self.verify_chain()
        else:
            self.channels[channel][key] = value
            self.verify_chain()
    
    # Validation functions for various settings
    def verify_chain(self):
        self.status["pico_setup_verify"] = self.pico_util.verify_channels_defined(self.channels, self.timebase, self.resolution)
        for chan in self.channels:
            self.channels[chan]["verified"] = self.pico_util.verify_channel_settings(self.channels[chan])
        self.status["channel_setup_verify"] = self.pico_util.set_channel_verify_flag(self.channels)
        self.status["channel_trigger_verify"] = self.pico_util.verify_trigger(self.channels, self.trigger)
        self.status["capture_settings_verify"] = self.pico_util.verify_capture(self.capture)
    
    @run_on_executor
    def run_capture(self,ignore):
        capture_instance = PicoBlockDevice(self.handle)
        s = self.status
        error_count = 0
        close = None
        status_list = [s["pico_setup_verify"],s["channel_setup_verify"],s["channel_trigger_verify"],s["capture_settings_verify"]]
        for status in status_list:
            if status != 0:
                error_count += 1

        if ((error_count == 0) and (s["openunit"]  == -1)):
            with self.lock:
                logging.debug("Settings verified, running capture")
                if self.status["openunit"] == -1:
                    self.status["openunit"] = capture_instance.open_unit(self.resolution)
                for channel in self.channels:
                    chan = self.channels[channel]
                    capture_instance.set_channel("channel_"+(str(chan["channel_id"])),chan["channel_id"],chan["active"],
                                        chan["coupling"],chan["range"],chan["offset"])

                trig = self.trigger
                ps_channels = {0:'a',1:'b',2:'c',3:'d'}
                range = self.channels[ps_channels[trig["source"]]]["range"]
                capture_instance.set_simple_trigger(trig["source"],range,trig["threshold"]) #Make trigger take direction/delay/auto_trigger

                cap = self.capture
                capture_instance.run_block(self.timebase,cap["pre_trig_samples"],cap["post_trig_samples"],cap["n_captures"])
                close = capture_instance.stop_scope()
                print(f'Close return status: {close}')
        else:
            logging.debug(f'{error_count} settings have issues, not running capture')
        
        if close == 0:
            self.status["openunit"] = -1
        logging.debug(f'Close status = {close} | openunit = {self.status["openunit"]}')

    def start_live_view(self):
        self.live_capture_running = True

    def stop_live_view(self):
        pass

    def update_poll(self):
        self.test_view.run_block()
        logging.debug(f'')
        # if self.live_capture_running:
        #     with self.lock:

        logging.debug(f'Current data in liveview : {self.streaming_buffer[0]} of length: {len(self.streaming_buffer[0])}')
        pass

    def cleanup(self):
        logging.debug("Stoping picoscope services and closing device")
        self.pico_block_device.stop_scope()

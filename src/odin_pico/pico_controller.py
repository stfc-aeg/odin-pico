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
from odin_pico.pico_util import PicoUtil 

class PicoController():
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self,lock,handle):
        self.handle = ctypes.c_int16(handle)
        self.pico_block_device = PicoBlockDevice(np.int16(self.handle))
        self.pico_util = PicoUtil()
        self.lock = lock

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

        self.verify_chain()

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
        # call verify chain

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
    def run_capture(self):
        # Set channels up
        if self.status["openunit"] == -1:
            self.status["openunit"] = self.pico_block_device.open_unit(self.resolution)
        for channel in self.channels:
            chan = self.channels[channel]
            self.pico_block_device.set_channel("channel_"+(str(chan["channel_id"])),chan["channel_id"],chan["active"],
                                  chan["coupling"],chan["range"],chan["offset"])
        
        # Set trigger 
        trig = self.trigger
        ps_channels = {0:'a',1:'b',2:'c',3:'d'}
        range = self.channels[ps_channels[trig["source"]]]["range"]
        self.pico_block_device.set_simple_trigger(trig["source"],range,trig["threshold"])

        # Run Block command
        cap = self.capture
        self.pico_block_device.run_block(self.timebase,cap["pre_trig_samples"],cap["post_trig_samples"],cap["n_captures"])

    def update_poll(self):
        pass

    def cleanup(self):
        logging.debug("Stoping picoscope services and closing device")
        self.stop_status = ps.ps5000aStop(self.handle)
        self.close_status = ps.ps5000aCloseUnit(self.handle)

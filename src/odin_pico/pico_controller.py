import numpy as np

import logging
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from concurrent.futures import thread
from tornado.concurrent import run_on_executor
from concurrent import futures

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

from odin_pico.pico_util import PicoUtil
from odin_pico.pico_config import DeviceConfig
from odin_pico.pico_status import Status
from odin_pico.pico_device import PicoDevice
from odin_pico.buffer_manager import BufferManager
from odin_pico.file_writer import FileWriter

class PicoController():
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self,lock):
        self.lock = lock

        self.util = PicoUtil()
        self.dev_conf = DeviceConfig()
        self.pico_status = Status()
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf,self.buffer_manager)

        self.pico = PicoDevice(self.dev_conf,self.pico_status,self.buffer_manager)

        self.connection_attempted = -1

        adapter_status = ParameterTree ({
            'open_unit': (partial(self.get_status_value, "open_unit"), None),
            'pico_setup_verify': (partial(self.get_status_value, "pico_setup_verify"), None),
            'channel_setup_verify': (partial(self.get_status_value, "channel_setup_verify"), None),
            'channel_trigger_verify': (partial(self.get_status_value, "channel_trigger_verify"), None),
            'capture_settings_verify': (partial(self.get_status_value, "capture_settings_verify"), None)
        })

        pico_commands = ParameterTree ({
            'run_capture': (lambda: self.connection_attempted, self.run_capture)
        })

        self.chan_params = {}
        for channel in self.util.channel_names:
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
            'active': (partial(self.get_trigger_value, "active"), partial(self.set_trigger_value, "active")),
            'auto_trigger': (partial(self.get_trigger_value, "auto_trigger_ms"), partial(self.set_trigger_value, "auto_trigger_ms")),
            'direction': (partial(self.get_trigger_value, "direction"), partial(self.set_trigger_value, "direction")),
            'delay': (partial(self.get_trigger_value, "delay"), partial(self.set_trigger_value, "delay")),
            'source': (partial(self.get_trigger_value, "source"), partial(self.set_trigger_value, "source")),
            'threshold': (partial(self.get_trigger_value, "threshold"), partial(self.set_trigger_value, "threshold"))
        })

        pico_capture = ParameterTree ({
            'pre_trig_samples': (partial(self.get_capture_value, "pre_trig_samples"), partial(self.set_capture_value, "pre_trig_samples")),
            'post_trig_samples': (partial(self.get_capture_value, "post_trig_samples"), partial(self.set_capture_value, "post_trig_samples")),
            'n_captures': (partial(self.get_capture_value, "n_captures"), partial(self.set_capture_value, "n_captures"))
        })
        
        pico_mode = ParameterTree ({
            'resolution': (partial(self.get_mode_value, "resolution"), partial(self.set_mode_value, "resolution")),
            'timebase': (partial(self.get_mode_value, "timebase"), partial(self.set_mode_value, "timebase"))
        })

        pico_settings = ParameterTree ({
            'mode': pico_mode,
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
    # reduce into one function that uses getattr and gets passed a "path" such as trigger 
    # getattr(dev_conf,path)["active"] where path = "trigger"
    def get_channel_value(self,channel,value):
        return self.dev_conf.channels[channel][value]
    
    def get_trigger_value(self,value):
        return self.dev_conf.trigger[value]

    def get_capture_value(self,value):
        return self.dev_conf.capture[value]

    def get_mode_value(self,value):
        return self.dev_conf.mode[value]
    
    def get_status_value(self,value):
        return self.pico_status.status[value]
    
    def set_channel_value(self, channel, key, value):
        if key in self.util.channel_dicts:
            if value in self.util.channel_dicts[key]:
                self.dev_conf.channels[channel][key] = value
        else:
            self.dev_conf.channels[channel][key] = value
        self.verify_chain()

    def set_trigger_value(self,key,value):
        if key in self.util.trigger_dicts:
            if value in self.util.trigger_dicts[key]:
                self.dev_conf.trigger[key] = value
        else:
            self.dev_conf.trigger[key] = value
        self.verify_chain()

    def set_mode_value(self,key,value):
        if key in self.util.mode_dicts:
            if value in self.util.mode_dicts[key]:
                self.dev_conf.mode[key] = value
        else:
            self.dev_conf.mode[key] = value
        self.verify_chain()

    def set_capture_value(self,key,value):
        self.dev_conf.capture[key] = value
        self.verify_chain()

    def verify_chain(self):
        pass
        self.pico_status.status["pico_setup_verify"] = self.util.verify_channels_defined(self.dev_conf.channels, self.dev_conf.mode)
        for chan in self.dev_conf.channels:
            self.dev_conf.channels[chan]["verified"] = self.util.verify_channel_settings(self.dev_conf.channels[chan])
        self.pico_status.status["channel_setup_verify"] = self.util.set_channel_verify_flag(self.dev_conf.channels)
        self.pico_status.status["channel_trigger_verify"] = self.util.verify_trigger(self.dev_conf.channels, self.dev_conf.trigger)
        self.pico_status.status["capture_settings_verify"] = self.util.verify_capture(self.dev_conf.capture)

    @run_on_executor
    def run_capture(self, value):
        logging.debug(f'Run capture function on thread')
        status_list = [self.pico_status.status["pico_setup_verify"], self.pico_status.status["channel_setup_verify"], 
                       self.pico_status.status["channel_trigger_verify"], self.pico_status.status["capture_settings_verify"]]
        for status in status_list:
            if status != 0:
                logging.debug(f'settings not verified, not running capture')
                return
        
        logging.debug(f'Running capture')
        if self.pico_status.status["open_unit"] != 0:
            self.pico.open_unit()
        self.pico.set_channels()
        self.pico.set_trigger()
        self.pico.assign_buffers()
        self.pico.run_block()
        self.file_writer.writeHDF5()
        self.pico.stop_scope()

    def update_poll(self):
        pass

    def cleanup(self):
        logging.debug("Stoping picoscope services and closing device")
    
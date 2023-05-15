import time
import numpy as np

import logging
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from concurrent.futures import thread
from tornado.concurrent import run_on_executor
from concurrent import futures

from odin_pico.pico_util import PicoUtil
from odin_pico.pico_config import DeviceConfig
from odin_pico.pico_status import Status
from odin_pico.pico_device import PicoDevice
from odin_pico.buffer_manager import BufferManager
from odin_pico.file_writer import FileWriter

class PicoController():
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self,lock,loop):
        self.lock = lock
        self.update_loop_active = loop
        self.lv_captures = 1

        self.util = PicoUtil()
        self.dev_conf = DeviceConfig()
        self.pico_status = Status()
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf,self.buffer_manager)
        self.pico = PicoDevice(self.dev_conf,self.pico_status,self.buffer_manager)

        self.connection_attempted = -1

        adapter_status = ParameterTree ({
            'settings_verified':(lambda: self.get_flag_value("verify_all"), None),
            'open_unit': (partial(self.get_status_value, "open_unit"), None),
            'pico_setup_verify': (partial(self.get_status_value, "pico_setup_verify"), None),
            'channel_setup_verify': (partial(self.get_status_value, "channel_setup_verify"), None),
            'channel_trigger_verify': (partial(self.get_status_value, "channel_trigger_verify"), None),
            'capture_settings_verify': (partial(self.get_status_value, "capture_settings_verify"), None)
        })

        pico_commands = ParameterTree ({
            'run_user_capture': (lambda: self.get_flag_value("user_capture"), self.start_user_capture)
        })

        self.chan_params = {}
        for channel in self.util.channel_names:
            self.chan_params[channel] = ParameterTree({
                'channel_id': (partial(self.get_channel_value, channel, "channel_id"), None),
                'active': (partial(self.get_channel_value, channel, "active"), partial(self.set_channel_value, channel, "active")),
                'verified': (partial(self.get_channel_value, channel,"verified"), None),
                'coupling': (partial(self.get_channel_value, channel, "coupling"), partial(self.set_channel_value, channel, "coupling")),
                'range': (partial(self.get_channel_value, channel, "range"), partial(self.set_channel_value, channel, "range")),
                'offset': (partial(self.get_channel_value, channel, "offset"), partial(self.set_channel_value, channel, "offset"))
                })

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

        live_view = ParameterTree ({
            'preview_channel': (lambda: self.get_dev_conf_value('preview_channel'), partial(self.set_dev_conf_value,'preview_channel')),
            'lv_data': (self.lv_data, None)
        })

        self.pico_param_tree = ParameterTree ({
            'status': adapter_status,
            'commands': pico_commands,
            'settings': pico_settings,
            'live_view': live_view
        })

        self.param_tree = ParameterTree ({
            'device': self.pico_param_tree
        })

        if self.update_loop_active:
            self.update_loop()
        self.verify_settings()

    # Return function for channel parameters to avoid late binding issues
    # reduce into one function that uses getattr and gets passed a "path" such as trigger 
    # getattr(dev_conf,path)["active"] where path = "trigger"
    #getattr
    def get_dev_conf_value(self,path):
        return getattr(self.dev_conf,path)

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

    def get_flag_value(self,value):
        return self.pico_status.flag[value]
    
    def set_dev_conf_value(self,path,value):
        setattr(self.dev_conf,path,value)
    
    def set_channel_value(self, channel, key, value):
        if key in self.util.channel_dicts:
            if value in self.util.channel_dicts[key]:
                self.dev_conf.channels[channel][key] = value
        else:
            self.dev_conf.channels[channel][key] = value

    def set_trigger_value(self,key,value):
        if key in self.util.trigger_dicts:
            if value in self.util.trigger_dicts[key]:
                self.dev_conf.trigger[key] = value
        else:
            self.dev_conf.trigger[key] = value

    def set_mode_value(self,key,value):
        if key in self.util.mode_dicts:
            if value in self.util.mode_dicts[key]:
                self.dev_conf.mode[key] = value
        else:
            self.dev_conf.mode[key] = value
        if key == "resolution":
            logging.debug(f'resolution change detected, setting flag')
            self.pico_status.flag["res_changed"] = True
            
    def set_capture_value(self,key,value):
        self.dev_conf.capture[key] = value

    def start_user_capture(self, value):
        self.pico_status.flag["user_capture"] = value
        logging.debug("Setting user_capture flag to true ")

    def verify_settings(self):
        self.pico_status.status["pico_setup_verify"] = self.util.verify_channels_defined(self.dev_conf.channels, self.dev_conf.mode)
        for chan in self.dev_conf.channels:
            self.dev_conf.channels[chan]["verified"] = self.util.verify_channel_settings(self.dev_conf.channels[chan])
        self.pico_status.status["channel_setup_verify"] = self.util.set_channel_verify_flag(self.dev_conf.channels)
        self.pico_status.status["channel_trigger_verify"] = self.util.verify_trigger(self.dev_conf.channels, self.dev_conf.trigger)
        self.pico_status.status["capture_settings_verify"] = self.util.verify_capture(self.dev_conf.capture)
        
        self.pico_status.flag["verify_all"] = self.set_verify_flag()

    def set_verify_flag(self):
        status_list = [self.pico_status.status["pico_setup_verify"], self.pico_status.status["channel_setup_verify"], 
                       self.pico_status.status["channel_trigger_verify"], self.pico_status.status["capture_settings_verify"]]
        for status in status_list:
            if status != 0:
                return False
        return True

    #@run_on_executor
    def run_capture(self):
        logging.debug(f'Run capture function called on update_loop thread')
        if self.pico_status.flag["verify_all"]:
            if self.pico_status.flag["res_changed"]:
                if self.pico_status.status["open_unit"] == 0:
                    self.pico.stop_scope()
                self.pico_status.flag["res_changed"] = False

            if self.pico_status.flag["user_capture"]:
                logging.debug(f'Settings verified - Running user defined capture')
                self.pico.run_setup()
                self.pico.run_block()
                self.file_writer.writeHDF5()
                self.buffer_manager.save_lv_data()
                self.pico_status.flag["user_capture"] = False
            else:
                logging.debug(f'Settings verified - Running live_view capture')
                self.pico.run_setup(self.lv_captures)
                self.pico.run_block(self.lv_captures)
                self.buffer_manager.save_lv_data()
        else:
            logging.debug(f'Settings invalid, passing capture function')

    # Add threading lock to set, add threading lock to functions that access pico device
    # Make run_lv_capture and run_capture seperate commands 
    # In run_lv_capture store the current value of captures and temporarily set it to 1 so the capture completes quickly so it can be sent to live view
    # once the "lv capture" has ran, set the captures value back to what it was set to
      
    def lv_data(self,*args):
        if args:
            pos = 0
        else:
            pos = (self.dev_conf.capture["n_captures"]-1)
        logging.debug(f'pos value =:{pos}')

        for c,b in zip(self.buffer_manager.lv_active_channels,self.buffer_manager.lv_channel_arrays):
            if (c == self.dev_conf.preview_channel):
                return b[-1][::10].tolist()
        return []

        # if self.dev_conf.preview_channel in self.buffer_manager.lv_active_channels:
        #     print(np.shape(self.buffer_manager.lv_active_channels[0]))
        #     return (self.buffer_manager.lv_channel_arrays[self.dev_conf.preview_channel][-1][::10].tolist())
        # else:
        #     return []

##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        
        while self.update_loop_active:
            self.run_capture()
            print(self.get_dev_conf_value('preview_channel'))

            time.sleep(1)
    
    def set_update_loop_state(self, state=bool):
        self.update_loop_active = state

    def cleanup(self):
        self.set_update_loop_state(False)
        self.pico.stop_scope()
        logging.debug("Stoping PicoScope services and closing device")

    def get(self, path):
        """Get the parameter tree. """ 

        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree. """

        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise PicoControllerError(e)
        self.verify_settings()      
 
class PicoControllerError(Exception):
    pass
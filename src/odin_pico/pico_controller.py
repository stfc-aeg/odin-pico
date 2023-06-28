import math
import time
import logging

from functools import partial
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.concurrent import run_on_executor
from concurrent import futures

from odin_pico.pico_util import PicoUtil
from odin_pico.pico_config import DeviceConfig
from odin_pico.pico_status import Status
from odin_pico.pico_device import PicoDevice
from odin_pico.buffer_manager import BufferManager
from odin_pico.file_writer import FileWriter
from odin_pico.analysis import PicoAnalysis

class PicoController():
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self,lock,loop,path):
        # Threading lock and control variables
        self.lock = lock
        self.update_loop_active = loop
        self.lv_captures = 1

        # Objects for handling configuration, data storage and representing the PicoScope 5444D
        self.dev_conf = DeviceConfig(path)
        self.pico_status = Status()
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf,self.buffer_manager) 
        self.analysis = PicoAnalysis(self.dev_conf, self.buffer_manager)
        self.pico = PicoDevice(self.dev_conf,self.pico_status,self.buffer_manager)
        self.util = PicoUtil()

        # ParameterTree's to represent different parts of the system
        adapter_status = ParameterTree ({
            'settings_verified': (lambda: self.get_flag_value("verify_all"), None),
            'open_unit': (lambda: self.get_status_value("open_unit"), None),
            'pico_setup_verify': (lambda: self.get_status_value("pico_setup_verify"), None),
            'channel_setup_verify': (lambda: self.get_status_value("channel_setup_verify"), None),
            'channel_trigger_verify': (lambda: self.get_status_value("channel_trigger_verify"), None),
            'capture_settings_verify': (lambda: self.get_status_value("capture_settings_verify"), None)
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

            #print(self.get_dev_conf_value('channels',channel,'active'))

        pico_trigger = ParameterTree ({
            'active': (lambda: self.get_trigger_value("active"), partial(self.set_trigger_value, "active")),
            'auto_trigger': (lambda: self.get_trigger_value("auto_trigger_ms"), partial(self.set_trigger_value, "auto_trigger_ms")),
            'direction': (lambda: self.get_trigger_value("direction"), partial(self.set_trigger_value, "direction")),
            'delay': (lambda: self.get_trigger_value("delay"), partial(self.set_trigger_value, "delay")),
            'source': (lambda: self.get_trigger_value("source"), partial(self.set_trigger_value, "source")),
            'threshold': (lambda: self.get_trigger_value("threshold"), partial(self.set_trigger_value, "threshold"))
        })

        pico_capture = ParameterTree ({
            'pre_trig_samples': (lambda: self.get_capture_value("pre_trig_samples"), partial(self.set_capture_value, "pre_trig_samples")),
            'post_trig_samples': (lambda: self.get_capture_value("post_trig_samples"), partial(self.set_capture_value, "post_trig_samples")),
            'n_captures': (lambda: self.get_capture_value("n_captures"), partial(self.set_capture_value, "n_captures"))
        })
        
        pico_mode = ParameterTree ({
            'resolution': (lambda: self.get_mode_value("resolution"), partial(self.set_mode_value, "resolution")),
            'timebase': (lambda: self.get_mode_value("timebase"), partial(self.set_mode_value, "timebase"))
        })

        pico_file = ParameterTree ({
            'folder_name': (lambda: self.get_value(self.dev_conf,'file','folder_name'), partial(self.set_file_value,'folder_name')),
            'file_name': (lambda: self.get_file_value("file_name"), partial(self.set_file_value,'file_name')),
            'file_path': (lambda: self.get_value(self.dev_conf,'file','file_path'), None),
            'curr_file_name': (lambda: self.get_value(self.dev_conf,'file','curr_file_name'), None),
            'last_write_success': (lambda: self.get_value(self.dev_conf,'file','last_write_success'), None)
        })

        pico_settings = ParameterTree ({
            'mode': pico_mode,
            'channels':{name: channel for (name, channel) in self.chan_params.items()},
            'trigger': pico_trigger,
            'capture': pico_capture,
            'file': pico_file,
        })

        live_view = ParameterTree ({
            'preview_channel': (lambda: self.get_dev_conf_value('preview_channel'), partial(self.set_dev_conf_value,'preview_channel')),
            'lv_data': (self.lv_data, None),
            'pha_data': (self.pha_data, None),
            'capture_count': (lambda: self.dev_conf.capture_run["live_cap_comp"], None),
            'captures_requested': (lambda: self.dev_conf.capture["n_captures"], None)
        })

        pico_commands = ParameterTree ({
            'run_user_capture': (lambda: self.get_flag_value("user_capture"), self.start_user_capture)
        })

        pico_flags = ParameterTree ({
            'abort_cap': (lambda: self.pico_status.flag["abort_cap"], self.abort_cap)
        })

        self.pico_param_tree = ParameterTree ({
            'status': adapter_status,
            'commands': pico_commands,
            'settings': pico_settings,
            'flags': pico_flags,
            'live_view': live_view
        })

        self.param_tree = ParameterTree ({
            'device': self.pico_param_tree
        })

        # Initalise the "update_loop" if control variable passed to the Pico_Controller is True
        if self.update_loop_active:
            self.update_loop()
        # Set initial state of the verification system
        self.verify_settings()

    # Function that takes a path as *args and traverses until it finds the value specified by the last key in *args
    def get_dev_conf_value(self, *args):
        value = self.dev_conf
        keys = [item for item in args]
        for key in keys:
            try:            
                value = getattr(value, key)
            except:
                if isinstance(value, dict):
                    value = value.get(key)
        return value
    
    def get_value(self, obj, *args):
        value = obj
        keys = [item for item in args]
        try:
            for key in keys:
                try:            
                    value = getattr(value, key)
                except:
                    if isinstance(value, dict):
                        value = value.get(key)
            return value
        except:
            return None

    def get_file_value(self, value):
        return self.dev_conf.file[value]    
    
    def get_channel_value(self, channel, value):
        return self.dev_conf.channels[channel][value]
    
    def get_trigger_value(self, value):
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

    def set_file_value(self,key,value):
        self.dev_conf.file[key] = value

    def set_capture_value(self,key,value):
        self.dev_conf.capture[key] = value

    def start_user_capture(self, value):
        self.pico_status.flag["user_capture"] = value

    def abort_cap(self, value):
        self.pico_status.flag["abort_cap"] = value

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
    
    def set_capture_run_limits(self):
        """ 
            Set the value for maximum amount of captures that can fit into
            the picoscope memory taking into account current user settings
            as well as setting the captures_remaning variable 
        """
        capture_samples = self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"]
        self.dev_conf.capture_run["caps_max"] = 100
       # self.dev_conf.capture_run["caps_max"] = math.floor(self.util.max_samples(self.dev_conf.mode["resolution"]) / capture_samples)
        self.dev_conf.capture_run["caps_remaining"] = self.dev_conf.capture["n_captures"]

    def set_capture_run_length(self):
        """
            Sets the captures to be completed in each "run" based on 
            the maximum allowed captures, and the amount of captures
            left to be collected
        """
        if self.dev_conf.capture_run["caps_remaining"] <= self.dev_conf.capture_run["caps_max"]:
            self.dev_conf.capture_run["caps_in_run"] = self.dev_conf.capture_run["caps_remaining"]
        else:
            self.dev_conf.capture_run["caps_in_run"] = self.dev_conf.capture_run["caps_max"]

    def set_capture_run_lv(self):
        self.dev_conf.capture_run["caps_max"] = self.lv_captures
        self.dev_conf.capture_run["caps_remaining"] = self.lv_captures
        self.dev_conf.capture_run["caps_in_run"] = self.lv_captures

    def run_capture(self):
        self.pico_status.flag["abort_cap"] = False
        if self.pico_status.flag["verify_all"]:
            # Detect if the device resolution has been changed, if so apply to picoscope
            if self.pico_status.flag["res_changed"]:
                if self.pico_status.status["open_unit"] == 0:
                    self.pico.stop_scope()
                self.pico_status.flag["res_changed"] = False

            # Run specific steps for user defined capture
            if self.pico_status.flag["user_capture"]:
                self.set_capture_run_limits()
                if self.pico.run_setup():
                    print("setup completed")
                    while self.dev_conf.capture_run["caps_comp"] < self.dev_conf.capture["n_captures"]:
                        print("\n\n\nentering capture loop")
                       
                    
                        
                        self.set_capture_run_length()
                        self.pico.assign_pico_memory()
                        print(self.dev_conf.capture_run)
                        self.pico.run_block()

                        self.dev_conf.capture_run["caps_comp"] += self.dev_conf.capture_run["caps_in_run"]
                        self.dev_conf.capture_run["caps_remaining"] -= self.dev_conf.capture_run["caps_in_run"]

                        self.analysis.PHA_one_peak()
                        self.buffer_manager.save_lv_data()
                    self.file_writer.writeHDF5()
                else:
                    print("error in setup")
                
                self.dev_conf.capture_run = self.util.set_capture_run_defaults()
                self.pico_status.flag["user_capture"] = False          
                
            # Run specific steps for live view capture
            else:
                #return
                print("entering liveview condition")
                self.set_capture_run_lv()
                if self.pico.run_setup(self.lv_captures):
                    self.pico.assign_pico_memory()
                    
                    self.pico.run_block(self.lv_captures)
                    self.analysis.PHA_one_peak()
                    self.buffer_manager.save_lv_data()
      
    def lv_data(self):
        for c,b in zip(self.buffer_manager.lv_active_channels,self.buffer_manager.lv_channel_arrays):
            if (c == self.dev_conf.preview_channel):
                return b[self.dev_conf.capture_run["caps_comp"]-1][::10].tolist()
        return []

    def pha_data(self):
        for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.pha_arrays):
            if (c == self.dev_conf.preview_channel):
                return b.tolist()

##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        """ """
        
        while self.update_loop_active:
            self.run_capture()
            time.sleep(0.2)
    
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
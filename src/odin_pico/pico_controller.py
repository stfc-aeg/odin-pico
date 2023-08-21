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

    def __init__(self, lock, loop, path):
        # Threading lock and control variables
        self.lock = lock
        self.update_loop_active = loop
        self.lv_captures = 1

        # Objects for handling configuration, data storage and representing the PicoScope 5444D
        self.dev_conf = DeviceConfig(path)
        self.pico_status = Status()
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf, self.buffer_manager, self.pico_status) 
        self.analysis = PicoAnalysis(self.dev_conf, self.buffer_manager, self.pico_status)
        self.pico = PicoDevice(self.dev_conf, self.pico_status, self.buffer_manager)
        self.util = PicoUtil()

        # ParameterTree's to represent different parts of the system
        adapter_status = ParameterTree({
            'settings_verified': (lambda: self.get_value(self.pico_status, 'flag', 'verify_all'), None),
            'open_unit': (lambda: self.get_value(self.pico_status, 'status', 'open_unit'), None),
            'pico_setup_verify': (lambda: self.get_value(self.pico_status, 'status', 'pico_setup_verify'), None),
            'channel_setup_verify': (lambda: self.get_value(self.pico_status, 'status', 'channel_setup_verify'), None),
            'channel_trigger_verify': (lambda: self.get_value(self.pico_status, 'status', 'channel_trigger_verify'), None),
            'capture_settings_verify': (lambda: self.get_value(self.pico_status, 'status', 'capture_settings_verify'), None)
        })

        self.chan_params = {}
        for channel in self.util.channel_names:
            self.chan_params[channel] = ParameterTree({
                'channel_id': (partial(self.get_value, self.dev_conf, 'channels', channel, 'channel_id'), None),
                'active': (partial(self.get_value, self.dev_conf, 'channels', channel, 'active'), partial(self.set_channel_value, channel, "active")),
                'verified': (partial(self.get_value, self.dev_conf, 'channels', channel, 'verified'), None),
                'coupling': (partial(self.get_value, self.dev_conf, 'channels', channel, 'coupling'), partial(self.set_channel_value, channel, "coupling")),
                'range': (partial(self.get_value, self.dev_conf, 'channels', channel, 'range'), partial(self.set_channel_value, channel, "range")),
                'offset': (partial(self.get_value, self.dev_conf, 'channels', channel, 'offset'), partial(self.set_channel_value, channel, "offset"))
                })

        pico_trigger = ParameterTree({
            'active': (lambda: self.get_value(self.dev_conf, 'trigger', 'active'), partial(self.set_trigger_value, "active")),
            'auto_trigger': (lambda: self.get_value(self.dev_conf, 'trigger', 'auto_trigger'), partial(self.set_trigger_value, "auto_trigger")),
            'direction': (lambda: self.get_value(self.dev_conf, 'trigger', 'direction'), partial(self.set_trigger_value, "direction")),
            'delay': (lambda: self.get_value(self.dev_conf, 'trigger', 'delay'), partial(self.set_trigger_value, "delay")),
            'source': (lambda: self.get_value(self.dev_conf, 'trigger', 'source'), partial(self.set_trigger_value, "source")),
            'threshold': (lambda: self.get_value(self.dev_conf, 'trigger', 'threshold'), partial(self.set_trigger_value, "threshold"))
        })

        pico_capture = ParameterTree({
            'pre_trig_samples': (lambda: self.get_value(self.dev_conf, 'capture', 'pre_trig_samples'), lambda v: self.set_value('capture', 'pre_trig_samples', obj=self.dev_conf, new_val=v)),
            'post_trig_samples': (lambda: self.get_value(self.dev_conf, 'capture', 'post_trig_samples'), lambda v: self.set_value('capture', 'post_trig_samples', obj=self.dev_conf, new_val=v)),
            'n_captures': (lambda: self.get_value(self.dev_conf, 'capture', 'n_captures'), lambda v: self.set_value('capture', 'n_captures', obj=self.dev_conf, new_val=v))
        })

        pico_mode = ParameterTree({
            'resolution': (lambda: self.get_value(self.dev_conf, 'mode', 'resolution'), partial(self.set_mode_value, "resolution")),
            'timebase': (lambda: self.get_value(self.dev_conf, 'mode', 'timebase'), partial(self.set_mode_value, "timebase")),
            'samp_time': (lambda: self.get_value(self.dev_conf, 'mode', 'samp_time'), None)
        })

        pico_file = ParameterTree({
            'folder_name': (lambda: self.get_value(self.dev_conf, 'file', 'folder_name'), lambda v: self.set_value('file', 'folder_name', obj=self.dev_conf, new_val=v)),
            'file_name': (lambda: self.get_value(self.dev_conf, 'file', 'file_name'), lambda v: self.set_value('file', 'file_name', obj=self.dev_conf, new_val=v)),
            'file_path': (lambda: self.get_value(self.dev_conf, 'file', 'file_path'), None),
            'curr_file_name': (lambda: self.get_value(self.dev_conf, 'file', 'curr_file_name'), None),
            'last_write_success': (lambda: self.get_value(self.dev_conf, 'file', 'last_write_success'), None)
        })

        pico_pha = ParameterTree({
            'num_bins': (lambda: self.get_value(self.dev_conf, 'pha', 'num_bins'), lambda v: self.set_value('pha', 'num_bins', obj=self.dev_conf, new_val=v)),
            'lower_range': (lambda: self.get_value(self.dev_conf, 'pha', 'lower_range'), lambda v: self.set_value('pha', 'lower_range', obj=self.dev_conf, new_val=v)),
            'upper_range': (lambda: self.get_value(self.dev_conf, 'pha', 'upper_range'), lambda v: self.set_value('pha', 'upper_range', obj=self.dev_conf, new_val=v))
        })

        pico_settings = ParameterTree({
            'mode': pico_mode,
            'channels': {name: channel for (name, channel) in self.chan_params.items()},
            'trigger': pico_trigger,
            'capture': pico_capture,
            'file': pico_file,
            'pha': pico_pha
        })

        live_view = ParameterTree({
            'preview_channel': (lambda: self.get_value(self.dev_conf, 'preview_channel'), lambda v: self.set_value('preview_channel', obj=self.dev_conf, new_val=v)),
            'lv_data': (self.lv_data, None),
            'pha_data': (self.pha_data, None),
            'capture_count': (lambda: self.get_value(self.dev_conf, 'capture_run', 'live_cap_comp'), None), 
            'captures_requested': (lambda: self.get_value(self.dev_conf, 'capture', 'n_captures'), None)
        })

        pico_commands = ParameterTree({
            'run_user_capture': (lambda: self.get_value(self.pico_status, 'flag', 'user_capture'), lambda v: self.set_value('flag', 'user_capture', obj=self.pico_status, new_val=v))
        })

        pico_flags = ParameterTree({
            'abort_cap': (lambda: self.get_value(self.pico_status, 'flag', 'abort_cap'), lambda v: self.set_value('flag', 'abort_cap', obj=self.pico_status, new_val=v)),
            'system_state': (lambda: self.get_value(self.pico_status, 'flag', 'system_state'), None)
        })

        self.pico_param_tree = ParameterTree({
            'status': adapter_status,
            'commands': pico_commands,
            'settings': pico_settings,
            'flags': pico_flags,
            'live_view': live_view
        })

        self.param_tree = ParameterTree({
            'device': self.pico_param_tree
        })

        # Initalise the "update_loop" if control variable passed to the Pico_Controller is True
        if self.update_loop_active:
            self.update_loop()
        # Set initial state of the verification system
        self.verify_settings()
   
    def get_value(self, obj, *args):
        """Takes an obj and a path as *args and traverses until it finds the value specified by the last key in *args and returns the value of that key"""
        
        value = obj
        keys = [item for item in args]
        try:
            for key in keys:
                try:          
                    value = getattr(value, key)
                except AttributeError:
                    if isinstance(value, dict):
                        value = value.get(key)
            return value
        except Exception:
            return None
       
    def set_value(self, *args, obj, new_val):
        """Takes an obj and a path and traverses until it finds the value specificed by the last key in *args and sets it to the new_val provided"""

        value = obj
        keys = [item for item in args]
        if not keys:
            return None
        try:
            for key in keys[:-1]:
                try:
                    value = getattr(value, key)
                except AttributeError:
                    if isinstance(value, dict):
                        value = value.get(key)
            
            final_key = keys[-1]
            try:
                setattr(value, final_key, new_val)
            except AttributeError:
                if isinstance(value, dict):
                    value[final_key] = new_val
        except Exception as e:
            print(f"Error: {e}")
    
    def set_channel_value(self, channel, key, value):
        """Function to set values for various different variables that are part of each channel the values are only applied if they are valid potential values"""

        if key in self.util.channel_dicts:
            if value in self.util.channel_dicts[key]:
                self.dev_conf.channels[channel][key] = value
        else:
            self.dev_conf.channels[channel][key] = value

    def set_trigger_value(self, key, value):
        """Function to set values for various different variables that are part of the trigger the values are only applied if they are valid potential values"""

        if key in self.util.trigger_dicts:
            if value in self.util.trigger_dicts[key]:
                self.dev_conf.trigger[key] = value
        else:
            self.dev_conf.trigger[key] = value

    def set_mode_value(self, key, value):
        """Function to set values for various different variables that are part of the mode the values are only applied if they are valid potential values"""

        if key in self.util.mode_dicts:
            if value in self.util.mode_dicts[key]:
                self.dev_conf.mode[key] = value
        else:
            self.dev_conf.mode[key] = value
        if key == "resolution":
            self.pico_status.flag["res_changed"] = True

    def verify_settings(self):
        """Verifies all picoscope settings, sets status of individual groups of settings"""

        self.pico_status.status["pico_setup_verify"] = self.util.verify_channels_defined(self.dev_conf.channels, self.dev_conf.mode)
        for chan in self.dev_conf.channels:
            self.dev_conf.channels[chan]["verified"] = self.util.verify_channel_settings(self.dev_conf.channels[chan])
        self.pico_status.status["channel_setup_verify"] = self.util.set_channel_verify_flag(self.dev_conf.channels)
        self.pico_status.status["channel_trigger_verify"] = self.util.verify_trigger(self.dev_conf.channels, self.dev_conf.trigger)
        self.pico_status.status["capture_settings_verify"] = self.util.verify_capture(self.dev_conf.capture)
        self.pico_status.flag["verify_all"] = self.set_verify_flag()

    def set_verify_flag(self):
        """Used by the verify_settings() function to return the Boolean value of the setting verified flag"""

        status_list = [self.pico_status.status["pico_setup_verify"], self.pico_status.status["channel_setup_verify"],
                       self.pico_status.status["channel_trigger_verify"], self.pico_status.status["capture_settings_verify"]]
        for status in status_list:
            if status != 0:
                return False
        return True
    
    def set_capture_run_limits(self):
        """Set the value for maximum amount of captures that can fit into the picoscope memory taking into account current user settings as well as setting the captures_remaning variable"""

        capture_samples = self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"]
        #self.dev_conf.capture_run["caps_max"] = 100
        self.dev_conf.capture_run["caps_max"] = math.floor(self.util.max_samples(self.dev_conf.mode["resolution"]) / capture_samples)
        self.dev_conf.capture_run["caps_remaining"] = self.dev_conf.capture["n_captures"]

    def set_capture_run_length(self):
        """Sets the captures to be completed in each "run" based on the maximum allowed captures, and the amount of captures left to be collected"""

        if self.dev_conf.capture_run["caps_remaining"] <= self.dev_conf.capture_run["caps_max"]:
            self.dev_conf.capture_run["caps_in_run"] = self.dev_conf.capture_run["caps_remaining"]
        else:
            self.dev_conf.capture_run["caps_in_run"] = self.dev_conf.capture_run["caps_max"]

    def set_capture_run_lv(self):
        """Sets the capture variables to collect a single trace for LiveView"""

        self.dev_conf.capture_run["caps_max"] = self.lv_captures
        self.dev_conf.capture_run["caps_remaining"] = self.lv_captures
        self.dev_conf.capture_run["caps_in_run"] = self.lv_captures

    def calc_samp_time(self):
        """Calculates the sample interval based on the resolution and timebase"""

        if self.dev_conf.mode["resolution"] == 0:
            if ((self.dev_conf.mode["timebase"]) >= 0 and (self.dev_conf.mode["timebase"] <= 2)):
                self.dev_conf.mode["samp_time"] = (math.pow(2, self.dev_conf.mode["timebase"]) / (1000000000))
            else:
                self.dev_conf.mode["samp_time"] = ((self.dev_conf.mode["timebase"] - 2) / (125000000))
        elif self.dev_conf.mode["resolution"] == 1:
            if ((self.dev_conf.mode["timebase"]) >= 1 and (self.dev_conf.mode["timebase"] <= 3)):
                self.dev_conf.mode["samp_time"] = (math.pow(2, self.dev_conf.mode["timebase"] - 1) / (500000000))
            else:
                self.dev_conf.mode["samp_time"] = ((self.dev_conf.mode["timebase"] - 3) / (62500000))

    def run_capture(self):
        """Responsible for telling the picoscope to collect and return data"""

        self.calc_samp_time()
        self.pico_status.flag["abort_cap"] = False
        if self.pico_status.flag["verify_all"]:
            self.check_res()
            if self.pico_status.flag["user_capture"]:
                self.user_cap()
            else:
                self.lv_cap()
        if ((self.pico_status.status["open_unit"] == 0) and (self.pico_status.flag["verify_all"] is False)):
            self.pico_status.flag["system_state"] = "Connected to Picoscope, Idle"

    def check_res(self):
        """Detect if the device resolution has been changed, if so apply to picoscope"""

        if self.pico_status.flag["res_changed"]:
            if self.pico_status.status["open_unit"] == 0:
                self.pico.stop_scope()
            self.pico_status.flag["res_changed"] = False

    def user_cap(self):
        """Run the appropriate steps for starting a user defined capture"""

        self.set_capture_run_limits()
        if self.pico.run_setup():
            while self.dev_conf.capture_run["caps_comp"] < self.dev_conf.capture["n_captures"]:
                self.set_capture_run_length()
                self.pico.assign_pico_memory()
                self.pico.run_block()
                self.dev_conf.capture_run["caps_comp"] += self.dev_conf.capture_run["caps_in_run"]
                self.dev_conf.capture_run["caps_remaining"] -= self.dev_conf.capture_run["caps_in_run"]
                self.analysis.PHA_one_peak()
                self.buffer_manager.save_lv_data()
            self.file_writer.writeHDF5()
        self.dev_conf.capture_run = self.util.set_capture_run_defaults()
        self.pico_status.flag["user_capture"] = False

    def lv_cap(self):
        """Run the appropriate steps for starting a live view capture"""

        self.set_capture_run_lv()
        if self.pico.run_setup(self.lv_captures):
            self.pico.assign_pico_memory()
            self.pico.run_block()
            self.buffer_manager.save_lv_data()
      
    def lv_data(self):
        """Returns array of the last captured trace, that has been stored in the buffer manager, for a channel selected by the user in the UI"""

        array = None

        for c, b in zip(self.buffer_manager.lv_active_channels, self.buffer_manager.lv_channel_arrays):
            if (c == self.dev_conf.preview_channel):
                array = b#[::10]
        if array is None:
            return []
        else:
            return array

    def pha_data(self):
        """ Returns array of the last calculated PHA, that has been stored in the buffer manager, for a channel selected by the user in the UI"""

        array = None

        for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.lv_pha):
            if (c == self.dev_conf.preview_channel):
                array = b.tolist()
        if array is None:
            return []
        else:
            return array

##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        """Function that is called in an executor thread, responsible for calling the run_capture function at timed intervals """
        
        while self.update_loop_active:
            self.run_capture()
            time.sleep(0.2)

    def set_update_loop_state(self, state=bool):
        """Sets the state of the update_loop in the executor thread"""

        self.update_loop_active = state

    def cleanup(self):
        """Responsible for making sure the picoscope is closed cleanly when the adapter is shutdown"""

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
from picosdk.ps5000a import ps5000a as ps
import ctypes
import numpy as np


class PicoUtil():
    def __init__(self):
        ######
        # Revisit to see if channels_names, channel_names_dict and ps_channels can be replaced with just ps_channels
        self.channel_names = ['a', 'b', 'c', 'd']
        self.channel_names_dict = {0:'a',1:'b',2:'c',3:'d'}
        ######

        self.range_offsets = {
            0 : 0.25,
            1 : 0.25,
            2 : 0.25,
            3 : 0.25,
            4 : 0.25,
            5 : 2.5,
            6 : 2.5,
            7 : 2.5,
            8 : 20,
            9 : 20,
            10 : 20
        }

        self.ps_resolution = {ps.PS5000A_DEVICE_RESOLUTION[val] : val for val in [
            "PS5000A_DR_8BIT",
            "PS5000A_DR_12BIT"
        ]}

        self.ps_coupling = {ps.PS5000A_COUPLING[val] : val for val in [
            "PS5000A_AC",
            "PS5000A_DC"
        ]}

        self.ps_channel = {ps.PS5000A_CHANNEL[val] : val for val in [
            "PS5000A_CHANNEL_A",
            "PS5000A_CHANNEL_B",
            "PS5000A_CHANNEL_C",
            "PS5000A_CHANNEL_D"
        ]}

        self.ps_direction = {ps.PS5000A_THRESHOLD_DIRECTION[val] : val for val in [
            "PS5000A_ABOVE",
            "PS5000A_BELOW",
            "PS5000A_RISING",
            "PS5000A_FALLING",
            "PS5000A_RISING_OR_FALLING"
        ]}

        self.ps_range = {ps.PS5000A_RANGE[val] : val for val in [
            "PS5000A_10MV",
            "PS5000A_20MV",
            "PS5000A_50MV",
            "PS5000A_100MV",
            "PS5000A_200MV",
            "PS5000A_500MV",
            "PS5000A_1V",
            "PS5000A_2V",
            "PS5000A_5V",
            "PS5000A_10V",
            "PS5000A_20V"
        ]}

        self.trigger_dicts = {
            "source":self.ps_channel,
            "direction":self.ps_direction
        }

        self.channel_dicts = {
            "coupling":self.ps_coupling,
            "range":self.ps_range
        }
        
        self.mode_dicts = {
            "resolution":self.ps_resolution
        }
        
    def get_range_value_mv(self,key):
        range_values = {
            0 : 10,
            1 : 20,
            2 : 50,
            3 : 100,
            4 : 200,
            5 : 500,
            6 : 1000,
            7 : 2000,
            8 : 5000,
            9 : 10000,
            10 : 20000
        }
        if key in range_values:
            return range_values[key]
    
    def set_mode_defaults(self):
        mode = {
            "handle" : ctypes.c_int16(0),
            "resolution" : 0,
            "timebase" : 0,
            
        }
        return mode
    
    def set_flag_defaults(self):
        flag = {
            "verify_all": False,
            "res_changed": False,
            "range_changed": False,
            "user_capture": False
        }
        return flag
        
    def set_trigger_defaults(self):
        trigger = {
            "active": False,
            "source": 0,
            "threshold": 0,
            "direction": 0,
            "delay": 0,
            "auto_trigger_ms": 0
        }
        return trigger
    
    def set_ps_defaults(self):
        status = {
            "open_unit": -1,
            "stop": -1,
            "close": -1
        }
        return status

    def set_rbs_defaults(self):
        status = {
            "block_check": ctypes.c_int16(0),
            "block_ready": ctypes.c_int16(0)
        }
        return status       

    def set_status_defaults(self):
        status = {
            "open_unit": -1,
            "stop": -1,
            "close": -1,
            "block_check": ctypes.c_int16(0),
            "block_ready": ctypes.c_int16(0),
            "pico_setup_verify": -1,
            "pico_setup_complete": -1,
            "channel_setup_verify": -1,
            "channel_setup_complete": -1,
            "channel_trigger_verify": -1,
            "channel_trigger_complete": -1,
            "capture_settings_verify": -1,
            "capture_settings_complete": -1,
        }
        return status
    
    def set_channel_defaults(self,name,id):
        channel = {
            "channel_id": id,
            "name": name,
            "active": False,
            "verified": False,
            "coupling": 0,
            "range": 0, 
            "offset": 0.0
        }
        return channel
    
    def set_capture_defaults(self):
        capture = {
            "pre_trig_samples": 0,
            "post_trig_samples": 0,
            "n_captures": 0
        }
        return capture

    def set_meta_data_defaults(self):
        meta_data = {
            "max_adc": ctypes.c_uint16(),
            "max_samples": ctypes.c_int32(),
            "total_cap_samples": ctypes.c_int32(),
            "samples_per_seg": ctypes.c_int32(0)
        }
        return meta_data
    
    def set_file_defaults(self,path):
        file = {
            "file_name": '',
            "folder_name": '',
            "file_path": path,
            "curr_file_name": '',
            "last_write_success": False,
        }
        return file
    
    def verify_channels_defined(self, channels, mode):
        channel_count = 0
        for chan in channels:
            if channels[chan]["active"] == True:
                channel_count += 1

        if mode["resolution"] == 1:
            if (mode["timebase"] < 1):
                return -1
            elif (mode["timebase"] == 1 and channel_count >0 and channel_count <2):
                return 0
            elif (mode["timebase"] == 2 and channel_count >0 and channel_count <3):
                return 0
            elif (mode["timebase"] >= 3 and channel_count >0 and channel_count <=4):
                return 0
            else:
                return -1
            
        if mode["resolution"] == 0:
            if (mode["timebase"] < 0):
                return -1
            elif (mode["timebase"] == 0 and channel_count >0 and channel_count <2):
                return 0 
            elif (mode["timebase"] == 1 and channel_count >0 and channel_count <3):
                return 0
            elif (mode["timebase"] >= 2 and channel_count >0 and channel_count <=4):
                return 0
            else:
                return -1
        
        if channel_count == 0:
            return -1
        
    def verify_channel_settings(self, chan):
        limit = self.range_offsets[chan["range"]]
        if (chan["offset"] >= (-limit) and chan["offset"] <= limit):
            return True
        else:
            return False

    def set_channel_verify_flag(self, channels):
        error_count = 0
        for chan in channels:
            if (channels[chan]["active"] == True) and (channels[chan]["verified"] == False):
                error_count += 1
        if error_count == 0:
            return 0
        else: 
            return -1
        
    def verify_trigger(self,channels,trigger):
        source_channel_info = channels[self.channel_names_dict[trigger["source"]]]
        if not(source_channel_info["active"]):
            return -1 
        if (trigger["threshold"] > self.get_range_value_mv(source_channel_info["range"])):
            return -1
        if not(trigger["delay"] >= 0 and trigger["delay"] <= 4294967295):
            return -1
        if not(trigger["auto_trigger_ms"] >= 0 and trigger["auto_trigger_ms"] <= 32767):
            return -1
        return 0 
    
    def verify_capture(self, capture):
        total_samples = capture["pre_trig_samples"] + capture["post_trig_samples"]
        if (total_samples < 1):
            return -1
        if (capture["n_captures"] <= 0):
            return -1
        if ((total_samples * capture["n_captures"]) > 50000000):
            return -1
        return 0


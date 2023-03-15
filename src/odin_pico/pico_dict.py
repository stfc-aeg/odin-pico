class PsDictUtil():

    def __init__(self):
        pass

    def ps_resolution(self,key):
        resolution = {
            0 : "PS5000A_DR_8BIT",
            1 : "PS5000A_DR_12BIT"
        }
        return(self.try_dict(resolution,key))

    def ps_coupling(self,key):
        coupling = {
            0 : "PS5000A_AC",
            1 : "PS5000A_DC"
        }
        return(self.try_dict(coupling,key))

    def ps_range(self,key):
        range = {
            0 : "PS5000A_10MV",
            1 : "PS5000A_20MV",
            2 : "PS5000A_50MV",
            3 : "PS5000A_100MV",
            4 : "PS5000A_200MV",
            5 : "PS5000A_500MV",
            6 : "PS5000A_1V",
            7 : "PS5000A_2V",
            8 : "PS5000A_5V",
            9 : "PS5000A_10V",
            10 : "PS5000A_20V",
        }
        return(self.try_dict(range,key))

        
    def ps_direction(self,key):
        direction = {
            0 : "PS5000A_ABOVE",
            1 : "PS5000A_BELOW",
            2 : "PS5000A_RISING",
            3 : "PS5000A_FALLING",
            4 : "PS5000A_RISING_OR_FALLING"
        }  
        return(self.try_dict(direction,key))
    
    def ps_channels(self,key):
        channels = {
            0 : "PS5000A_CHANNEL_A",
            1 : "PS5000A_CHANNEL_B",
            2 : "PS5000A_CHANNEL_C",
            3 : "PS5000A_CHANNEL_D",
        }
        return(self.try_dict(channels,key))

    
    def try_dict(self,dict,key):
        try:
            val = dict[key]
            print("Key is valid: ",val)
            return True
        except:
            print("Key",key,"is invalid:")
            return False
        
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
            10 : 20000,
        }
        try:
            val = range_values[key]
            return val
        except:
            return None
        
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

    def set_status_defaults(self):
        status = {
            "openunit": -1,
            "pico_setup_verify": -1,
            "pico_setup_complete": -1,
            "channel_setup_verify": -1,
            "channel_setup_complete": -1,
            "channel_trigger_verify": -1,
            "channel_trigger_complete": -1,
            "capture_settings_verify": -1,
            "capture_settings_complete": -1,
            "stop": -1,
            "close": -1
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

        





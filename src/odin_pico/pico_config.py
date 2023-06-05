import ctypes
from odin_pico.pico_util import PicoUtil

class DeviceConfig():
    def __init__(self, path):
        self.util = PicoUtil()

        # self.mode = self.util.set_mode_defaults()
        # self.trigger = self.util.set_trigger_defaults()
        # self.capture = self.util.set_capture_defaults()
        # self.preview_channel = 0
        # self.channels = {}
        # i = 0
        # for name in self.util.channel_names:
        #     self.channels[name] = self.util.set_channel_defaults(name,i)
        #     i += 1
        
        # self.meta_data = self.util.set_meta_data_defaults()
        self.file = self.util.set_file_defaults(path)

        self.mode = {
            "handle" : ctypes.c_int16(0),
            "resolution" : 1,
            "timebase" : 2,
        }
        self.trigger = {
            "active": True,
            "source": 0,
            "threshold": 0,
            "direction": 2,
            "delay": 0,
            "auto_trigger_ms": 0
        }

        self.capture = {
            "pre_trig_samples": 0,
            "post_trig_samples": 100000,
            "n_captures": 3
        }

        self.preview_channel = 0

        self.channels = {}
        i = 0
        for name in self.util.channel_names:
            self.channels[name] = {
            "channel_id": i,
            "name": name,
            "active": False,
            "verified": False,
            "coupling": 0,
            "range": 10, 
            "offset": 0.0
        }
            i += 1
        
        self.meta_data = self.util.set_meta_data_defaults()
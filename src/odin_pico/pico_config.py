import ctypes
import json
import os
from odin_pico.pico_util import PicoUtil

class DeviceConfig():
    def __init__(self, path):
        self.util = PicoUtil()

        self.mode = self.util.set_mode_defaults()
        self.trigger = self.util.set_trigger_defaults()
        self.capture = self.util.set_capture_defaults()
        self.capture_run = self.util.set_capture_run_defaults()
        self.preview_channel = 0
        self.channels = {}
        i = 0
        for name in self.util.channel_names:
            self.channels[name] = self.util.set_channel_defaults(name,i)
            i += 1
        
        self.meta_data = self.util.set_meta_data_defaults()
        self.file = self.util.set_file_defaults(path)
        self.pha = self.util.set_pha_defaults()
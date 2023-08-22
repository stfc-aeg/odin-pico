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

    def to_dict(self):
        """Convert the DeviceConfig object to a dictionary."""
        return {
            'mode': self.mode,
            'trigger': self.trigger,
            'capture': self.capture,
            'capture_run': self.capture_run,
            'preview_channel': self.preview_channel,
            'channels': self.channels,
            'meta_data': self.meta_data,
            'file': self.file,
            'pha': self.pha,
        }
    
    def load_from_dict(self, preset_data):
        """Load the DeviceConfig object from a dictionary."""
        self.mode = preset_data['mode']
        self.trigger = preset_data['trigger']
        self.capture = preset_data['capture']
        self.capture_run = preset_data['capture_run']
        self.preview_channel = preset_data['preview_channel']
        self.channels = preset_data['channels']
        self.meta_data = preset_data['meta_data']
        self.file = preset_data['file']
        self.pha = preset_data['pha']

    def save_preset(config, preset_name, folder_path='presets'):
        """Save DeviceConfig object as a JSON file."""
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        preset_path = os.path.join(folder_path, f"{preset_name}.json")
        with open(preset_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=4)
    
    def load_preset(preset_name, folder_path='presets'):
        """Load DeviceConfig object from a JSON file."""
        preset_path = os.path.join(folder_path, f"{preset_name}.json")
        if os.path.exists(preset_path):
            with open(preset_path, 'r') as f:
                preset_data = json.load(f)
            return DeviceConfig(preset_data=preset_data)
        else:
            raise FileNotFoundError(f"Preset '{preset_name}' not found.")
    
    def list_presets(folder_path='presets'):
        """List all available presets in the given folder."""
        if not os.path.exists(folder_path):
            return []

        all_files = os.listdir(folder_path)
        preset_files = [f[:-5] for f in all_files if f.endswith('.json')]  # Removing the .json extension to get the preset name
        return preset_files

        # self.mode = {
        #     "handle" : ctypes.c_int16(0),
        #     "resolution" : 1,
        #     "timebase" : 2,
        #     "samp_time": 0
        # }
        # self.trigger = {
        #     "active": True,
        #     "source": 0,
        #     "threshold": 0,
        #     "direction": 2,
        #     "delay": 0,
        #     "auto_trigger_ms": 0
        # }

        # self.capture = {
        #     "pre_trig_samples": 0,
        #     "post_trig_samples": 100000,
        #     "n_captures": 3
        # }

        # self.preview_channel = 0

        # self.channels = {}
        # i = 0
        # for name in self.util.channel_names:
        #     self.channels[name] = {
        #     "channel_id": i,
        #     "name": name,
        #     "active": False,
        #     "verified": False,
        #     "coupling": 0,
        #     "range": 10, 
        #     "offset": 0.0
        # }
        #     i += 1
        
        # self.meta_data = self.util.set_meta_data_defaults()

        # self.pha = self.util.set_pha_defaults()
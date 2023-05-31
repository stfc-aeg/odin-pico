import ctypes
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import h5py

from odin_pico.pico_config import DeviceConfig

class BufferManager():
    def __init__(self, dev_conf=DeviceConfig(None)):
        self.dev_conf = dev_conf
        self.overflow = None
        self.active_channels = []
        self.channel_arrays = []
        self.pha_arrays = []
        
        self.lv_active_channels = []
        self.lv_channel_arrays = []
        self.lv_pha = []

    def generate_arrays(self, *args):
        if args:
            n_captures = args[0]
        else:
            n_captures = self.dev_conf.capture["n_captures"]

        self.overflow = (ctypes.c_int16 * n_captures)()
        self.clear_arrays()
        for chan in self.dev_conf.channels:
            if (self.dev_conf.channels[chan]["active"] == True):
                self.active_channels.append(self.dev_conf.channels[chan]["channel_id"])
        
        samples=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])
        for i in range(len(self.active_channels)):
            self.channel_arrays.append(np.zeros(shape=(n_captures,samples), dtype=np.int16))

    def save_lv_data(self):
        self.lv_active_channels = self.active_channels
        self.lv_channel_arrays = self.channel_arrays
        self.lv_pha = self.pha_arrays

    def clear_arrays(self):
        while (len(self.active_channels)) > 0:
            self.active_channels.pop()
        while (len(self.channel_arrays)) > 0:
            self.channel_arrays.pop()
        while (len(self.pha_arrays)) > 0:
            self.pha_arrays.pop()




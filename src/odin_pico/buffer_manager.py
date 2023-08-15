import ctypes
from datetime import datetime
import time
import numpy as np
import matplotlib.pyplot as plt
import h5py

from odin_pico.pico_config import DeviceConfig
from odin_pico.pico_util import PicoUtil

from picosdk.functions import adc2mV


class BufferManager():
    def __init__(self, dev_conf=DeviceConfig(None)):
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.overflow = None
        self.active_channels = []
        self.channel_arrays = []
        self.pha_arrays = []
        self.trigger_times = []
        
        self.lv_active_channels = []
        self.lv_channel_arrays = []
        self.lv_pha = []

    def generate_arrays(self, *args):
        """
            Creates the local buffers that the picoscope will eventually be mapped 
            onto for data collection
        """
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
        """
            Return a live view of traces being captured
        """
        self.lv_active_channels = self.active_channels

        for c, b in zip(self.active_channels, self.pha_arrays):
            range = self.dev_conf.channels[self.util.channel_names_dict[c]]["range"]
            #self.lv_pha.append(adc2mV(b[0], range, self.dev_conf.meta_data["max_adc"]))
            self.lv_pha.append(b)

        for c, b in zip(self.active_channels, self.channel_arrays):
            range = self.dev_conf.channels[self.util.channel_names_dict[c]]["range"]
            self.lv_channel_arrays.append(adc2mV(b[-1], range, self.dev_conf.meta_data["max_adc"]))

            #time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager
        """
        arrays = [self.active_channels, self.channel_arrays, self.pha_arrays,self.trigger_times,
                  self.lv_active_channels, self.lv_channel_arrays]#, self.lv_pha]
        for array in arrays:
            array.clear()
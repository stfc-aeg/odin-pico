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
            Temporary solution to return a live view of traces being captured
        """
        # start = time.time()
        self.lv_active_channels = self.active_channels
        self.lv_pha = self.pha_arrays
        # self.lv_channel_arrays = self.channel_arrays
        # end = time.time()
        # print(f'Time to copy data is: {end-start}')

        start = time.time()
        for c, b in zip(self.active_channels, self.channel_arrays):
            # Gets the "range" value for each channel inside the active_channels array
            range = self.dev_conf.channels[self.util.channel_names_dict[c]]["range"]

            # Print channel_array before conversion
            print(f'array before calc: {b[0]}')

            # test array of fake, but realistic data, 8k samples for chosen settings is around 50mV
            test_array = [8217, 8251, 8251, -8235, -8218, -8218]
            print(f'test_array converted = :{adc2mV(test_array, range, self.dev_conf.meta_data["max_adc"])}')

            print(f'range for adc2mV: {range} | max_ADC: {self.dev_conf.meta_data["max_adc"]}')

            self.lv_channel_arrays.append(adc2mV(b[0], range, self.dev_conf.meta_data["max_adc"]))

        end = time.time()
        print(f'Time to calculate data is: {end-start}')


    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager
        """
        while (len(self.active_channels)) > 0:
            self.active_channels.pop()
        while (len(self.channel_arrays)) > 0:
            self.channel_arrays.pop()
        while (len(self.pha_arrays)) > 0:
            self.pha_arrays.pop()
        while (len(self.trigger_times)) > 0:
            self.trigger_times.pop()
        while (len(self.lv_active_channels)) > 0:
            self.lv_active_channels.pop()
        while (len(self.lv_channel_arrays)) > 0:
            self.lv_channel_arrays.pop()
        while (len(self.lv_pha)) > 0:
            self.lv_pha.pop()




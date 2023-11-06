import ctypes
import numpy as np
import logging

from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.pico_util import PicoUtil

from functools import partial

from picosdk.functions import adc2mV

class BufferManager():
    def __init__(self, dev_conf=DeviceConfig()):
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.overflow = None
        self.channels = [self.dev_conf.channel_a, self.dev_conf.channel_b, self.dev_conf.channel_c, self.dev_conf.channel_d]
        self.active_channels = [False] * 4
        self.np_channel_arrays = []
        self.pha_arrays = []
        self.trigger_times = []
        
        self.lv_active_channels = [False] * 4
        self.lv_channel_arrays = []
        self.chan_range = [0] * 4
        self.lv_pha = []
        self.lv_channels_active = []

    def generate_arrays(self, *args):
        """
            Creates the local buffers that the picoscope will eventually be mapped
            onto for data collection.
        """
        if args:
            n_captures = args[0]
        else:
            n_captures = self.dev_conf.capture.n_captures

        self.overflow = (ctypes.c_int16 * n_captures)()
        self.clear_arrays()

        for chan in self.channels:
            if (chan.active is True):
                self.active_channels.append(chan.channel_id)

        for chan in range(4):
            if (self.channels[chan].live_view is True):
                self.lv_channels_active.append(chan)
        
        samples = self.dev_conf.capture.pre_trig_samples + self.dev_conf.capture.post_trig_samples
        for i in range(len(self.lv_active_channels)):
            if self.lv_active_channels[i] == True:
                self.np_channel_arrays.append(np.zeros(shape=(n_captures, samples), dtype=np.int16))

    def save_lv_data(self):
        """
            Return a live view of traces being captured.
        """

        for c, b in zip(self.active_channels, self.pha_arrays):
            for chan in self.channels:
                if chan.channel_id == c:
                    chan_range = chan.range
            #self.lv_pha.append(adc2mV(b[0], chan_range, self.dev_conf.meta_dat.max_adc))
            self.lv_pha.append(b)

        for item in self.lv_active_channels:
            self.chan_range[item] = self.channels[item].range
        
        temp = []

        for c, b in zip(self.lv_channels_active, self.np_channel_arrays):
            values = adc2mV(b[-1], self.chan_range[c], self.dev_conf.meta_data.max_adc)
            if all(values) != 0:
                if (values) != [0]:
                    if (values) != []:
                        temp.append(values)
                        print("Values", values)
                        # print(adc2mV(b[-1], self.chan_range[c], self.dev_conf.meta_data.max_adc))                                        
                    #     self.lv_channel_arrays.append("Error")
                    else:
                        temp.append("Error")
                        # print("Error")
                else:
                    temp.append("Error")
                    # print("Error")
            else:
                # print("Error")
                temp.append("Error")
            # else:
                # self.lv_channel_arrays.append(adc2mV(b[-1], self.chan_range[c], self.dev_conf.meta_data.max_adc))
        found = False
        for i in range(len(temp)):
            if temp[i] == "Error":
                found = True

        if found == False:
            if len(temp) != 0:
                ("Appending")
                print(self.lv_channel_arrays)
                print(temp)
                self.lv_channel_arrays = temp

            # if "Error" in temp:
            #     self.lv_channel_arrays = self.lv_channel_arrays
            # else:
            #     self.lv_channel_arrays = temp

        # for i in range(4):
        #     if self.lv_active_channels[i]:
        #         if all(adc2mV(self.np_channel_arrays[i][-1], self.chan_range[i], self.dev_conf.meta_data.max_adc)) == 0:
        #             self.lv_channel_arrays[(2 * c)] = ["Error"]
        #         else:
        #             self.lv_channel_arrays[(2 * c)] = adc2mV(self.np_channel_arrays[i][-1], self.chan_range[i], self.dev_conf.meta_data.max_adc)
        #     self.lv_channel_arrays[((2 * c) + 1)] = 



    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager.
        """
        arrays = [self.active_channels, self.pha_arrays, self.trigger_times, self.np_channel_arrays, 
                  self.lv_channels_active]#, self.lv_pha]
        for array in arrays:
            array.clear()
        self.chan_range = [0] * 4
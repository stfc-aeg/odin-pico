import ctypes
import numpy as np
import logging

from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.pico_util import PicoUtil

from picosdk.functions import adc2mV

class BufferManager():
    def __init__(self, dev_conf=DeviceConfig()):
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.overflow = None
        self.channels = [self.dev_conf.channel_a, self.dev_conf.channel_b, self.dev_conf.channel_c, self.dev_conf.channel_d]
        self.active_channels = [False] * 4
        self.channel_arrays = [0] * 4
        self.pha_arrays = []
        self.trigger_times = []
        
        self.lv_active_channels = [False] * 4
        self.lv_channel_array_a = []
        self.lv_channel_array_b = []
        self.lv_channel_array_c = []
        self.lv_channel_array_d = []
        self.lv_channel_arrays = [self.lv_channel_array_a, self.lv_channel_array_b,
                                  self.lv_channel_array_c,self.lv_channel_array_d]

        self.lv_pha = []

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
        
        samples = self.dev_conf.capture.pre_trig_samples + self.dev_conf.capture.post_trig_samples
#        for i in range(0,4):
#            if self.lv_active_channels[i] == True:
#                logging.debug("Appending.......")
#                self.lv_channel_arrays[i].append(np.zeros(shape=(n_captures,samples), dtype=np.int16))
#                print(self.lv_channel_arrays[i])

    def save_lv_data(self):
        """
            Return a live view of traces being captured.
        """
        self.lv_active_channels = [0] * 4

        for c, b in zip(self.active_channels, self.pha_arrays):
            for chan in self.channels:
                if chan.channel_id == c:
                    chan_range = chan.range
            #self.lv_pha.append(adc2mV(b[0], chan_range, self.dev_conf.meta_dat.max_adc))
            self.lv_pha.append(b)

        for i in range(0,4):
            if i == 0:
                chan_name = "channel_a"
            elif i == 1:
                chan_name = "channel_b"
            elif i == 2:
                chan_name = "channel_c"
            else:
                chan_name = "channel_d"

            
            if self.lv_active_channels[i] == True:
                self.lv_channel_arrays[i].append(adc2mV(self.lv_channel_arrays[i], chan_name, int(self.dev_conf.meta_data.max_adc)))
                print(self.lv_channel_arrays[i])


#        for c, b in zip(self.active_channels, self.channel_arrays):
#            for chan in self.channels:
#                if chan.channel_id == c:
#                    chan_range = chan.range
#            self.lv_channel_arrays.append(adc2mV(b[-1], chan_range, self.dev_conf.meta_data.max_adc))
            #time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager.
        """
        arrays = [self.active_channels, self.channel_arrays, self.pha_arrays, self.trigger_times,
                  self.lv_channel_arrays[0], self.lv_channel_arrays[1], self.lv_channel_arrays[2],
                  self.lv_channel_arrays[3]]#, self.lv_pha]
        for array in arrays:
            array.clear()
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
        self.lv_channel_arrays = [0] * 8
        self.chan_range = [0] * 4
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
        for i in range(len(self.lv_active_channels)):
            if self.lv_active_channels[i] == True:
                self.channel_arrays[i] = (np.zeros(shape=(n_captures,samples), dtype=np.int16))
       
#        for i in range(0,4):
#            if self.lv_active_channels[i] == True:
#                logging.debug("Appending.......")
#                self.lv_channel_arrays[i].append(np.zeros(shape=(n_captures,samples), dtype=np.int16))
#                print(self.lv_channel_arrays[i])

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

#        for i in range(0,4):
#            if i == 0:
#                chan_name = "channel_a"
#            elif i == 1:
#                chan_name = "channel_b"
#            elif i == 2:
#                chan_name = "channel_c"
#            else:
#                chan_name = "channel_d"

        print(len(self.lv_channel_arrays))

#            if self.lv_active_channels[i] == True:
#                self.lv_channel_arrays[i].append(adc2mV(self.lv_channel_arrays[i], chan_name, int(self.dev_conf.meta_data.max_adc)))
#                print(self.lv_channel_arrays[i])

        for item in self.lv_active_channels:
            if self.lv_active_channels[item] == True:
                self.chan_range[item] = self.channels[item].range


#        temp = 0
#        for chan in self.channels:
#            if chan.channel_id == self.active_channels[temp]:
#                chan_range = chan.range
#            temp += 1

        for channel in range(4):
            if self.lv_active_channels[channel]:
                logging.debug(len(self.lv_channel_arrays))
                logging.debug(len(self.channel_arrays))
                logging.debug(self.channel_arrays[0])
                logging.debug(self.channel_arrays)
#                logging.debug(self.channel_arrays[0][-1])

                self.lv_channel_arrays[(2 * channel)] = adc2mV(self.channel_arrays[channel][-1], self.chan_range[channel], self.dev_conf.meta_data.max_adc)
                self.lv_channel_arrays[((2 * channel)+1)] = channel

        logging.debug(self.lv_channel_arrays)

        for temp in range(0,8):
            logging.debug(self.lv_channel_arrays[temp])

#        for c, b in zip(self.active_channels, self.channel_arrays):
#            for chan in self.channels:
#                if chan.channel_id == c:
#                    chan_range = chan.range
            
#            self.lv_channel_arrays[(2 * chan)] = adc2mV(b[-1], chan_range, self.dev_conf.meta_data.max_adc)
#            self.lv_channel_arrays.append((adc2mV(b[-1], chan_range, self.dev_conf.meta_data.max_adc)))
#            self.lv_channel_arrays[((2 * chan)+1)] = c
#            self.lv_channel_arrays.append(c)
#            logging.debug(self.lv_channel_arrays)
#            logging.debug(self.lv_channel_arrays[0])
            #time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager.
        """
        arrays = [self.active_channels, self.pha_arrays, self.trigger_times,]#, self.lv_pha]
        for array in arrays:
            array.clear()
        self.lv_channel_arrays = [0] * 8
        self.chan_range = [0] * 4
        self.channel_arrays = [0] * 4
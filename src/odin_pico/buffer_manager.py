import ctypes
import numpy as np

from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.pico_util import PicoUtil

from picosdk.functions import adc2mV

class BufferManager():
    def __init__(self, dev_conf=DeviceConfig()):
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.overflow = None
        self.channels = [self.dev_conf.channel_a, self.dev_conf.channel_b, self.dev_conf.channel_c, self.dev_conf.channel_d]
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
        for i in range(len(self.active_channels)):
            self.channel_arrays.append(np.zeros(shape=(n_captures,samples), dtype=np.int16))

    def save_lv_data(self):
        """
            Return a live view of traces being captured.
        """
        self.lv_active_channels = self.active_channels

        for c, b in zip(self.active_channels, self.pha_arrays):
            for chan in self.channels:
                if chan.channel_id == c:
                    chan_range = chan.range
            #self.lv_pha.append(adc2mV(b[0], chan_range, self.dev_conf.meta_dat.max_adc))
            self.lv_pha.append(b)

        for c, b in zip(self.active_channels, self.channel_arrays):
            for chan in self.channels:
                if chan.channel_id == c:
                    chan_range = chan.range
            self.lv_channel_arrays.append(adc2mV(b[-1], chan_range, self.dev_conf.meta_data.max_adc))
            #time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager.
        """
        arrays = [self.active_channels, self.channel_arrays, self.pha_arrays, self.trigger_times,
                  self.lv_active_channels, self.lv_channel_arrays] #, self.lv_pha]
        for array in arrays:
            array.clear()
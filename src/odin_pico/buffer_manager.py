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
        self.active_channels = []
        self.np_channel_arrays = []
        self.pha_arrays = []
        self.trigger_times = []

        # Holds currrent PHA and LV data        
        self.pha_counts = []
        self.lv_channel_arrays = []

        # Holds ranges and offsets for active channels
        self.chan_range = [0] * 4
        self.chan_offsets = [0] * 4

        self.lv_channels_active = []
        self.pha_channels_active = [False] * 4
        self.pha_active_channels = []
        self.current_pha_channels = []
        self.bin_edges = []
        self.pha_counts = [[]] * 4
        self.pha_changed = False
        self.clear_pha = False

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

        samples = self.dev_conf.capture.pre_trig_samples + self.dev_conf.capture.post_trig_samples

        for chan in self.channels:
            if (chan.active is True):
                self.active_channels.append(chan.channel_id)
                if (chan.live_view is True):
                    self.lv_channels_active.append(chan.channel_id)
                if (chan.pha_active is True):
                    self.pha_channels_active[chan.channel_id] = True
                    self.pha_active_channels.append(chan.channel_id)

        for chan in self.channels:
            if(chan.active is True):
                self.np_channel_arrays.append(np.zeros(shape=(n_captures, samples), dtype=np.int16))

    def save_lv_data(self):
        """
            Return a live view of traces being captured.
            """

        # Find ranges and offsets for all channels
        for channel in range(4):
            self.chan_range[channel] = self.channels[channel].range
            self.chan_offsets[channel] = self.channels[channel].offset

        all_current_pha_data = []
        for c, b in zip(self.active_channels, self.pha_arrays):
            all_current_pha_data.append(b.tolist())

        if len(all_current_pha_data) > 0:
            self.bin_edges = ((all_current_pha_data[0])[0])

        pha_counts = []
        for array in range((len(all_current_pha_data))):
            pha_counts.append((all_current_pha_data[array])[1])

        if (self.clear_pha):
            self.pha_counts = [[]] * 4
            self.clear_pha = False

        for channel in range(len(pha_counts)):
            if (len(self.pha_counts[self.current_pha_channels[channel]])) != 0:
                self.pha_counts[self.current_pha_channels[channel]] = np.array(pha_counts[channel]) + np.array(self.pha_counts[self.current_pha_channels[channel]])
                self.pha_counts[self.current_pha_channels[channel]] = ((self.pha_counts[self.current_pha_channels[channel]]).tolist())
            else:
                self.pha_counts[self.current_pha_channels[channel]] = pha_counts[channel]

        current_lv_array = []
        for c, b in zip(self.lv_channels_active, self.np_channel_arrays):

            # Find current data, along with channel range and offset
            values = adc2mV(b[-1], self.chan_range[c], self.dev_conf.meta_data.max_adc)
            current_offset = self.chan_offsets[c]
            current_range = self.util.get_range_value_mv(self.chan_range[c])
            offset_key = ((current_offset/100) * current_range)

            # Adjust values for offset, unless offset is 0
            if current_offset != 0:
                for value in range(len(values)):
                    values[value] = values[value] + offset_key

            current_lv_array.append(values)
        # Replaces current data as long as new data is not blank
        if current_lv_array != []:
            self.lv_channel_arrays = current_lv_array

    def clear_arrays(self):
        """
            Removes previously created buffers from the buffer_manager.
        """
        arrays = [self.active_channels, self.trigger_times, self.np_channel_arrays, 
                  self.lv_channels_active, self.pha_active_channels]
        for array in arrays:
            array.clear()
        self.chan_range = [0] * 4
        self.chan_offsets = [0] * 4
        self.pha_channels_active = [False] * 4
"""Buffer manager which prepares and accepts buffers for the PicoScope."""

import ctypes
import math
import numpy as np
from picosdk.functions import adc2mV
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.pico_util import PicoUtil


class BufferManager:
    """Class which manages the buffers that are filled with data by the PicoScope."""

    def __init__(self, dev_conf=DeviceConfig()):
        """Initialise the BufferManager Class."""
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.overflow = None
        self.channels = [
            self.dev_conf.channel_a,
            self.dev_conf.channel_b,
            self.dev_conf.channel_c,
            self.dev_conf.channel_d,
        ]
        self.active_channels = []
        self.np_channel_arrays = []
        self.pha_arrays = []
        self.trigger_times = []

        # Holds currrent PHA and LV data
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
        self.lv_range = 0

    def generate_arrays(self):
        """Create the buffers that the picoscope will be mapped onto for data collection."""
        self.clear_arrays()

        # Cycle through channels, checking if they are active, and then PHA and LV active
        for chan in self.channels:
            if chan.active is True:
                self.active_channels.append(chan.channel_id)
                if chan.live_view is True:
                    self.lv_channels_active.append(chan.channel_id)
                if chan.pha_active is True:
                    self.pha_channels_active[chan.channel_id] = True
                    self.pha_active_channels.append(chan.channel_id)

        # Set amount of captures the scope will expect
        n_captures = math.trunc(
            self.dev_conf.capture_run.caps_max / len(self.active_channels)
        )

        self.overflow = (ctypes.c_int16 * n_captures)()

        samples = (
            self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples
        )

        # Create buffers, which will be recycled throughout
        for chan in self.channels:
            if chan.active is True:
                self.np_channel_arrays.append(
                    np.zeros(shape=(n_captures, samples), dtype=np.int16)
                )

    def generate_tb_arrays(self):
        """Create the buffers that the PicoScope uses during time-based data collection."""
        n_captures = self.dev_conf.capture_run.caps_in_run

        self.overflow = (ctypes.c_int16 * n_captures)()

        samples = (
            self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples
        )

        # Create recyclable buffers
        for chan in self.channels:
            if chan.active is True:
                self.np_channel_arrays.append(
                    np.zeros(shape=(n_captures, samples), dtype=np.int16)
                )

    def accumulate_pha(self, chan, pha_data):
        """Add the new PHA data to the previous data, if there is any data."""
        current_pha_data = (self.pha_arrays[pha_data]).tolist()
        self.bin_edges = current_pha_data[0]
        pha_counts = (current_pha_data)[1]

        # Adds PHA to previous data, unless there is no previous data
        if len(self.pha_counts[chan]) != 0:
            self.pha_counts[chan] = np.array(pha_counts) + np.array(
                self.pha_counts[chan]
            )
            self.pha_counts[chan] = self.pha_counts[chan].tolist()
        else:
            self.pha_counts[chan] = pha_counts

    def check_channels(self):
        """Check which channels are active, LV active and PHA active."""
        for chan in self.channels:
            if chan.active is True:
                self.active_channels.append(chan.channel_id)
                if chan.live_view is True:
                    self.lv_channels_active.append(chan.channel_id)
                if chan.pha_active is True:
                    self.pha_channels_active[chan.channel_id] = True
                    self.pha_active_channels.append(chan.channel_id)

    def save_lv_data(self):
        """Return a live view of traces being captured."""
        # Find ranges and offsets for all channels
        for channel in range(4):
            self.chan_range[channel] = self.channels[channel].range
            self.chan_offsets[channel] = self.channels[channel].offset

        current_lv_array = []

        for c, b in zip(self.lv_channels_active, self.np_channel_arrays):
            # Find current data, along with channel range and offset
            values = adc2mV(
                b[(self.dev_conf.capture_run.caps_in_run - 1)],
                self.chan_range[c],
                self.dev_conf.meta_data.max_adc,
            )
            # current_offset = self.chan_offsets[c]
            # current_range = self.util.get_range_value_mv(self.chan_range[c])
            # offset_key = (current_offset / 100) * current_range

            # # Adjust values for offset, unless offset is 0
            # if current_offset != 0:
            #     for value in range(len(values)):
            #         values[value] = values[value] + offset_key

            current_lv_array.append(values)

        # Replaces current data as long as new data is not blank
        if current_lv_array != []:
            self.lv_channel_arrays = current_lv_array

    def clear_arrays(self):
        """Remove previously created buffers from the buffer_manager."""
        arrays = [
            self.active_channels,
            self.trigger_times,
            self.np_channel_arrays,
            self.lv_channels_active,
            self.pha_active_channels,
        ]
        for array in arrays:
            array.clear()
        self.chan_range = [0] * 4
        self.chan_offsets = [0] * 4
        self.pha_channels_active = [False] * 4

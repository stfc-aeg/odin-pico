"""Buffer manager which prepares and accepts buffers for the PicoScope."""

import ctypes
import logging
import math
import numpy as np
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.pico_util import PicoUtil

class BufferManager:
    """Class which manages the buffers that are filled with data by the PicoScope."""

    def __init__(self, channels=[], dev_conf=DeviceConfig()):
        """Initialise the BufferManager Class."""
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.overflow = None
        self.channels = channels
        self.active_channels = []
        self.np_channel_arrays = []
        self.pha_arrays = []
        self.trigger_times = []

        # Holds currrent PHA and LV data
        self.lv_channel_arrays = []

        self.lv_channels_active = []
        self.pha_channels_active = [False] * 4
        self.pha_active_channels = []
        self.current_pha_channels = []
        self.bin_edges = []
        self.pha_counts = [[]] * 4
        self.lv_range = 0

    def generate_arrays(self, *args):
        """Create the buffers that the picoscope will be mapped onto for data collection."""
        self.clear_arrays()
        self.check_channels()
        if args:
            n_captures = args[0]
        else:
            n_captures = self.dev_conf.capture.n_captures
        
        self.overflow = (ctypes.c_int16 * n_captures)()

        samples = (self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples)

        for i in range(len(self.active_channels)):
            self.np_channel_arrays.append(np.zeros(shape=(n_captures, samples), dtype=np.int16))

    def generate_tb_arrays(self):
        """Create the buffers that the PicoScope uses during time-based data collection."""
        n_captures = self.dev_conf.capture_run.caps_in_run

        self.overflow = (ctypes.c_int16 * n_captures)()

        samples = (
            self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples
        )

        # Create recyclable buffers
        for i in range(len(self.active_channels)):
            self.np_channel_arrays.append(
                np.zeros(shape=(n_captures,samples), dtype=np.int16)
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
            if chan.active:
                self.active_channels.append(chan.channel_id)
                if chan.live_view:
                    self.lv_channels_active.append(chan.channel_id)
                if chan.pha_active:
                    self.pha_channels_active[chan.channel_id] = True
                    self.pha_active_channels.append(chan.channel_id)

    def save_lv_data(self):
        """Return a live view of traces being captured."""
        self.lv_channel_arrays = []

        for c, b in zip(self.active_channels, self.np_channel_arrays):
            # Find current data, along with channel range and offset
            values = PicoUtil.adc2mV(
                b[(self.dev_conf.capture_run.caps_in_run - 1)],
                self.channels[c].range,
                self.dev_conf.meta_data.max_adc,
            ).tolist()
            if self.channels[c].live_view:
                self.lv_channel_arrays.append(values)

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
        self.pha_channels_active = [False] * 4
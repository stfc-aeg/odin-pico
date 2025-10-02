"""File which analyses the data extracted from the PicoScope."""

import logging
import numpy as np

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.pico_config import DeviceConfig
from odin_pico.DataClasses.pico_status import DeviceStatus


class PicoAnalysis:
    """Picoscope data analysis class.

    This class implements analysis methods that manipulate the data captured by
    the picoscope.
    """

    def __init__(
        self,
        dev_conf=DeviceConfig(),
        buffer_manager=BufferManager(),
        pico_status=DeviceStatus(),
    ):
        """Initialise PicoAnalysis class."""
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager
        self.pico_status = pico_status

    def pha_one_peak(self):
        """Analysis function - generates peak height distributions."""

        # Check if user has requested PHA counts to be cleared
        if self.dev_conf.pha.clear_pha:
            self.buffer_manager.reset_pha()
            self.dev_conf.pha.clear_pha = False

        # Select channels based on capture mode
        channels = (self.buffer_manager.active_channels
                    if self.pico_status.flags.user_capture
                    else self.buffer_manager.pha_active_channels)

        channel_key = {
            0: "channel_a",
            1: "channel_b",
            2: "channel_c",
            3: "channel_d",
        }

        # Calculate and store pha for relevant channels if they have been toggled by the user
        for chan in channels:
            if (getattr(self.dev_conf, channel_key[chan]).PHAToggled):
                self.get_pha_data(chan)

    def get_pha_data(self, channel):
        """Find the peaks in the data and send to the buffer manager."""
        # Get channel idx and captures for passed channel
        ch_idx = self.buffer_manager.active_channels.index(channel)
        captures = self.buffer_manager.np_channel_arrays[ch_idx]

        # Find peak value in each capture
        peak_values = captures.max(axis=1)

        # Histogram the counts against the bin_edges, within user defined ranges
        counts, bin_edges = np.histogram(
            peak_values,
            bins=self.dev_conf.pha.num_bins,
            range=(self.dev_conf.pha.lower_range, self.dev_conf.pha.upper_range),
        )

        # set bin edges
        self.buffer_manager.bin_edges = bin_edges[:-1]
        
        # Accumulate counts 
        self.buffer_manager.accumulate_pha(channel, counts)
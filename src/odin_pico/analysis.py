"""File which analyses the data extracted from the PicoScope."""

import numpy as np

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus


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
        self.bin_width = 250
        self.clear_pha = False

    def pha_one_peak(self):
        """Analysis function.

        Generates a distribution of peak heights in multiple
        traces and saves the information into a np.array in a dataset inside the file
        containing the raw adc_counts dataset.
        """
        # Clear the existing data and active channels
        self.buffer_manager.current_pha_channels.clear()
        self.buffer_manager.pha_arrays.clear()
        self.np_array = 0

        # Check if user has requested PHA counts to be cleared
        if self.clear_pha:
            self.buffer_manager.pha_counts = [[]] * 4
            self.clear_pha = False

        # Completes PHA for active channels if saving file, only PHA if LV mode
        if self.pico_status.flags.user_capture:
            for chan in self.buffer_manager.active_channels:
                self.get_pha_data(chan)
                self.buffer_manager.accumulate_pha(chan, self.np_array)
                self.np_array += 1
        else:
            for channel in self.buffer_manager.pha_active_channels:
                self.get_pha_data(channel)
                self.buffer_manager.accumulate_pha(channel, self.np_array)
                self.np_array += 1

    def get_pha_data(self, channel):
        """Find the peaks in the data and send to the buffer manager."""
        peak_values = []

        # Iterate through the channel array to expose each capture
        for i in range(self.dev_conf.capture_run.caps_in_run):
            data = (self.buffer_manager.np_channel_arrays[self.np_array])[i]

            # Find the peaks in each capture
            peak_pos = np.argmax(data)
            peak_values.append(data[peak_pos])

        # Use np.histogram to calculate counts for each bin, based on peak value data
        counts, bin_edge = np.histogram(
            peak_values,
            bins=self.dev_conf.pha.num_bins,
            range=(self.dev_conf.pha.lower_range, self.dev_conf.pha.upper_range),
        )

        # Send analysed data back to the buffer manager
        self.buffer_manager.pha_arrays.append(np.vstack((bin_edge[:-1], counts)))
        self.buffer_manager.current_pha_channels.append(channel)

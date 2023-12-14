import logging
import numpy as np 

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus

class PicoAnalysis():
    """
        Picoscope data analysis class.

        This class implements analysis methods that manipulate the data captured by
        the picoscope.
    """
    def __init__(self, dev_conf=DeviceConfig(), buffer_manager=BufferManager(), pico_status=DeviceStatus()):
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager
        self.pico_status = pico_status
        self.bin_width = 250

    def PHA_one_peak(self):
        """
            Analysis function that generates a distribution of peak heights in multiple
            traces and saves the information into a np.array in a dataset inside the file
            containing the raw adc_counts dataset
        """
        self.buffer_manager.current_pha_channels.clear()
        self.buffer_manager.pha_arrays.clear()
        
        for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.np_channel_arrays):
            peak_values = []

            # Iterate through the channel array to expose each capture
            for i in range(len(b)):
                data = b[i]

                # Find the peaks in each capture
                peak_pos = np.argmax(data)
                peak_values.append(data[peak_pos])

            # Use np.histogram to calculate counts for each bin, based on peak value data
            counts, bin_edge = np.histogram(peak_values, bins=self.dev_conf.pha.num_bins, range=(self.dev_conf.pha.lower_range, self.dev_conf.pha.upper_range))
            self.buffer_manager.pha_arrays.append(np.vstack((bin_edge[:-1], counts)))
            self.buffer_manager.current_pha_channels.append(c)

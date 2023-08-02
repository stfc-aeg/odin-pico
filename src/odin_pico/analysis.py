import logging
import h5py
import numpy as np 
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import math

from odin_pico.pico_config import DeviceConfig
from odin_pico.buffer_manager import BufferManager
from odin_pico.pico_status import Status

class PicoAnalysis():
    def __init__(self, dev_conf=DeviceConfig(None), buffer_manager=BufferManager(), pico_status=Status()):
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager
        self.pico_status = pico_status
        self.bin_width = 250

    def PHA_one_peak(self):
        self.pico_status.flag["system_state"] = "Connected to Picoscope, calculating PHA"
        ''' 
            Analysis function that generates a distribution of peak heights in multiple  
            traces and saves the information into a np.array in a dataset inside the file 
            containing the raw adc_counts dataset
        '''
        for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.channel_arrays):
            peak_values = []
            # Iterate through the channel array to expose each capture as b[i]
            for i in range(len(b)):
                data = b[i]
                # Find the peaks in each capture, using bin_width for grouping peaks
                peak_pos = np.argmax(data)
                peak_values.append(data[peak_pos])
            num_bins = 1024
            # Use np.histogram to calculate the counts for each bin, based on the peak_values data
            counts, bin_edge = np.histogram(peak_values, bins=num_bins, range=(0,(self.dev_conf.meta_data["max_adc"].value)))
            # Combine the bin_edge's and counts into one np.array
            self.buffer_manager.pha_arrays.append(np.vstack((bin_edge[:-1], counts)))
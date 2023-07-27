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

    def PHA(self):
        ''' 
            Analysis function that generates a distribution of peak heights in multiple  
            traces and saves the information into a np.array in a dataset inside the file 
            containing the raw adc_counts dataset
        '''
        # Zip through the active channels (each position has an int representing the channel) and channel arrays (each position is an array that contains all the captures for that channel)
        for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.channel_arrays):
            peak_values = []
            # Iterate through the channel array to expose each capture as b[i]
            for i in range(len(b)):
                data = b[i]
                # Find the peaks in each capture, using pre-determined bin_width for grouping peaks
                peak_pos, properties = find_peaks(data, distance = self.bin_width)
                for peak in peak_pos:
                    # Get the value at each peak position and append it to the peak_values array
                    peak_values.append(data[peak])
                print(f'Length of peak_values:{len(peak_values)}')
            # Calculate the number of bins required based on the bin_width
            #num_bins = math.ceil(np.max((self.dev_conf.meta_data["max_adc"].value)/self.bin_width))
            num_bins = 1024
            # Use np.histogram to calculate the counts for each bin, based on the peak_values data
            counts, bin_edge = np.histogram(peak_values, bins=num_bins)
            # Combine the bin_edge's and counts into one np.array
            self.buffer_manager.pha_arrays.append(np.vstack((bin_edge[:-1], counts)))

            #plt.plot(bin_edge[:-1], counts)
            #plt.show()

            # Is prominence relevant?
            #prom = math.ceil(max_adc_count*0.1) # max_adc returned from picoSDK is

    def PHA_one_peak(self):
        self.pico_status.flag["system_state"] = "Connected to Picoscope, calculating PHA"
        ''' 
            Analysis function that generates a distribution of peak heights in multiple  
            traces and saves the information into a np.array in a dataset inside the file 
            containing the raw adc_counts dataset
        '''
        # Zip through the active channels (each position has an int representing the channel) and channel arrays (each position is an array that contains all the captures for that channel)
        for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.channel_arrays):
            peak_values = []
            # Iterate through the channel array to expose each capture as b[i]
            for i in range(len(b)):
                data = b[i]
                # Find the peaks in each capture, using pre-determined bin_width for grouping peaks
                peak_pos = np.argmax(data)
                #print(f'peak pos:{peak_pos}')
                peak_values.append(data[peak_pos])
                #print(f'Length of peak_values:{len(peak_values)}')
            # Calculate the number of bins required based on the bin_width
            #num_bins = math.ceil(np.max((self.dev_conf.meta_data["max_adc"].value)/self.bin_width))
            num_bins = 1024
            # Use np.histogram to calculate the counts for each bin, based on the peak_values data
            counts, bin_edge = np.histogram(peak_values, bins=num_bins, range=(0,32768))
            # Combine the bin_edge's and counts into one np.array
            self.buffer_manager.pha_arrays.append(np.vstack((bin_edge[:-1], counts)))

            # Is prominence relevant?
            #prom = math.ceil(max_adc_count*0.1) # max_adc returned from picoSDK is

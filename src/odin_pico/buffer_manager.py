import ctypes
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import h5py

from odin_pico.pico_config import DeviceConfig

class BufferManager():
    def __init__(self, dev_conf=DeviceConfig()):
        self.dev_conf = dev_conf
        self.overflow = None
        self.active_channels = []
        self.channel_arrays = []

    def generate_arrays(self):
        self.overflow = (ctypes.c_int16 * self.dev_conf.capture["n_captures"])()
        self.clear_arrays()
        for chan in self.dev_conf.channels:
            if (self.dev_conf.channels[chan]["active"] == True):
                self.active_channels.append(self.dev_conf.channels[chan]["channel_id"])
        
        samples=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])
        for i in range(len(self.active_channels)):
            self.channel_arrays.append(np.zeros(shape=(self.dev_conf.capture["n_captures"],samples), dtype=np.int16))

    def plot(self):

        for c,b in zip(self.active_channels,self.channel_arrays):
            print(f'Channel {c}')
            for i in range(len(b)):
                print(b)
                buffer = b[i]
                plt.plot(buffer[:])
                plt.show()  

    def write(self):
        current_filename = (('/tmp/')+(str(datetime.now())).replace(' ','_')+'.hdf5')

        metadata = {

            #'max_adc': self.max_adc,
            'active_channels': self.active_channels[:]
            #'channel_ranges': self.channel_ranges[:]
        }

        with h5py.File(current_filename,'w') as f:
            metadata_group = f.create_group('metadata')
            for key, value in metadata.items():
                metadata_group.attrs[key] = value
            
            for c,b in zip(self.active_channels,self.channel_arrays):

                f.create_dataset(('adc_counts_'+str(c)), data = b)
                print(f'Creating dataset: adc_counts_{str(c)} with data : {b}')              

    def clear_arrays(self):
        print(f'Before pop:\nself.active_channels : {self.active_channels}\nself.channel_arrays : {self.channel_arrays} lengths: {(len(self.active_channels)),(len(self.channel_arrays))}')
        while (len(self.active_channels)) > 0:
            self.active_channels.pop()
        while (len(self.channel_arrays)) > 0:
            self.channel_arrays.pop()
        print(f'After pop:\nself.active_channels : {self.active_channels}\nself.channel_arrays : {self.channel_arrays} lengths: {(len(self.active_channels)),(len(self.channel_arrays))}')






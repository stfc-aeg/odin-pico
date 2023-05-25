import ctypes
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import h5py

from odin_pico.pico_config import DeviceConfig

class BufferManager():
    def __init__(self, dev_conf=DeviceConfig(None)):
        self.dev_conf = dev_conf
        self.overflow = None
        self.active_channels = []
        self.channel_arrays = []
        self.lv_active_channels = []
        self.lv_channel_arrays = []
        #self.last_pha = np.empty(shape=(2,0))

    def generate_arrays(self, *args):
        if args:
            n_captures = args[0]
        else:
            n_captures = self.dev_conf.capture["n_captures"]

        self.overflow = (ctypes.c_int16 * n_captures)()
        self.clear_arrays()
        for chan in self.dev_conf.channels:
            if (self.dev_conf.channels[chan]["active"] == True):
                self.active_channels.append(self.dev_conf.channels[chan]["channel_id"])
        
        samples=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])
        for i in range(len(self.active_channels)):
            self.channel_arrays.append(np.zeros(shape=(n_captures,samples), dtype=np.int16))

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

    def save_lv_data(self):
        self.lv_active_channels = self.active_channels
        self.lv_channel_arrays = self.channel_arrays

    def clear_arrays(self):
        while (len(self.active_channels)) > 0:
            self.active_channels.pop()
        while (len(self.channel_arrays)) > 0:
            self.channel_arrays.pop()




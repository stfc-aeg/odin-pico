from datetime import datetime
import logging
import h5py
import numpy as np
import time

from odin_pico.pico_config import DeviceConfig
from odin_pico.buffer_manager import BufferManager

class FileWriter():
    def __init__(self, dev_conf=DeviceConfig(), buffer_manager=BufferManager()):
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager

    def writeHDF5(self):
        current_filename = (('/tmp/')+(str(datetime.now())).replace(' ','_')+'.hdf5')

        metadata = {
            'active_channels' : self.buffer_manager.active_channels[:]
        }

        with h5py.File(current_filename, 'w') as f:
            metadata_group = f.create_group('metadata')
            for key, value in metadata.items():
                metadata_group.attrs[key] = value
            
            for c,b in zip(self.buffer_manager.active_channels,self.buffer_manager.channel_arrays):
                f.create_dataset(('adc_counts_'+str(c)), data = b)
                logging.debug(f'Creating dataset: adc_counts_{str(c)} with data : {b}')

        logging.debug(f'File writing complete')
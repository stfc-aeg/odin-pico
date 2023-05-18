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
        self.file_path_origin = "/"
        self.file_name = ""
        self.full_file_path = self.file_path_origin + self.file_name

    def writeHDF5(self):
        if self.file_name == "":
            self.file_name = ((self.file_path)+(str(datetime.now())).replace(' ','_')+'.hdf5')
            self.full_file_path = self.file_path_origin + self.file_name

        metadata = {
            'active_channels' : self.buffer_manager.active_channels[:]
        }

        with h5py.File(self.full_file_path, 'w') as f:
            metadata_group = f.create_group('metadata')
            for key, value in metadata.items():
                metadata_group.attrs[key] = value
           
            for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.channel_arrays):
                f.create_dataset(('adc_counts_'+str(c)), data = b)
                logging.debug(f'Creating dataset: adc_counts_{str(c)} with data : {b}')

        logging.debug(f'File writing complete')
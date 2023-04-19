import logging
import h5py
import numpy as np
import time

from odin_pico.pico_config import DeviceConfig

class FileWriter():
    def __init__(self, dev_conf=DeviceConfig()):
        self.dev_conf = dev_conf


        with h5py.File(self.current_filename,'w') as f:
            metadata_group = f.create_group('metadata')
            for key, value in metadata.items():
                metadata_group.attrs[key] = value

            for c,b in zip(self.active_channels,self.channel_buffers):

                f.create_dataset(('adc_counts_'+str(c)), data = b)
                print(f'Creating dataset: adc_counts_{str(c)} with data : {b}')

        logging.debug(f'File writing complete')
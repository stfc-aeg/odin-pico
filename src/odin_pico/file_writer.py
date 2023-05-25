from datetime import datetime
import logging
import os
import h5py
import numpy as np
import time

from odin_pico.pico_config import DeviceConfig
from odin_pico.buffer_manager import BufferManager

class FileWriter():
    def __init__(self, dev_conf=DeviceConfig(None), buffer_manager=BufferManager()):
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager

        if not (os.path.isdir(self.dev_conf.file["file_path"])):
            os.mkdir(self.dev_conf.file["file_path"])

    def writeHDF5(self):
        metadata = {
            'active_channels' : self.buffer_manager.active_channels[:]
        }

        logging.debug("Starting file writing")
        if (self.dev_conf.file["file_name"]) == "" or (os.path.isfile(self.dev_conf.file["file_path"] + self.dev_conf.file["folder_name"] + self.dev_conf.file["file_name"])):
            self.dev_conf.file["file_name"] = ((str(datetime.now())).replace(' ','_')+'.hdf5')

            logging.debug("File name blank, or taken: Generating File name")

        if self.dev_conf.file["folder_name"] != "" and self.dev_conf.file["folder_name"][-1] != "/":
            self.dev_conf.file["folder_name"] = self.dev_conf.file["folder_name"] + "/"
        
        if not (os.path.isdir(self.dev_conf.file["file_path"]+self.dev_conf.file["folder_name"])):
            os.mkdir(self.dev_conf.file["file_path"]+self.dev_conf.file["folder_name"])
            logging.debug(f'Folder name does not exist, creating')

        if not (self.dev_conf.file["file_name"][-5:] == ".hdf5"):
            self.dev_conf.file["file_name"] = self.dev_conf.file["file_name"] + ".hdf5"

        self.dev_conf.file["curr_file_name"] = (self.dev_conf.file["file_path"] + self.dev_conf.file["folder_name"] + self.dev_conf.file["file_name"])
        logging.debug(f'Full file path: {self.dev_conf.file["curr_file_name"]}')  

        try:
            with h5py.File((self.dev_conf.file["curr_file_name"]), 'w') as f:
                metadata_group = f.create_group('metadata')
                for key, value in metadata.items():
                    metadata_group.attrs[key] = value
            
                for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.channel_arrays):
                    f.create_dataset(('adc_counts_'+str(c)), data = b)
                    logging.debug(f'Creating dataset: adc_counts_{str(c)} with data : {b}')
        except Exception as e: 
            logging.debug(f'Exception caught:{e}')
            self.dev_conf.file["last_write_success"] = False
            return

        logging.debug(f'File writing finished successfully')
        self.dev_conf.file["last_write_success"] = True
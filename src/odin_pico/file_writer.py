from dataclasses import asdict
from datetime import datetime
import logging
import os
import h5py
import numpy as np
import time

from odin_pico.buffer_manager import BufferManager
from odin_pico.pico_util import PicoUtil
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus

class FileWriter():
    def __init__(self, dev_conf=DeviceConfig(), buffer_manager=BufferManager(), pico_status=DeviceStatus()):
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager
        self.pico_status = pico_status
        self.util = PicoUtil()

        if not (os.path.isdir(self.dev_conf.file.file_path)):
            os.mkdir(self.dev_conf.file.file_path)

    def writeHDF5(self):
        self.pico_status.flags.system_state = "Connected to Picoscope, Writing hdf5 File"

        metadata = self.util.flatten_metadata_dict({
            'active_channels' : self.buffer_manager.active_channels[:],
            'channel_a' : asdict(self.dev_conf.channel_a),
            'channel_b' : asdict(self.dev_conf.channel_b),
            'channel_c' : asdict(self.dev_conf.channel_c),
            'channel_d' : asdict(self.dev_conf.channel_d),
            'trigger' : asdict(self.dev_conf.trigger),
            'resolution' : self.dev_conf.mode.resolution,
            'timebase' : self.dev_conf.mode.timebase
        })

        # logging.debug("Starting file writing")
        if (self.dev_conf.file.file_name) == "" or (os.path.isfile(self.dev_conf.file.file_path + self.dev_conf.file.folder_name + self.dev_conf.file.file_name)):
            self.dev_conf.file.file_name = ((str(datetime.now())).replace(' ','_')+'.hdf5')

            # logging.debug("File name blank, or taken: Generating File name")

        if self.dev_conf.file.folder_name != "" and self.dev_conf.file.folder_name[-1:] != "/":
            self.dev_conf.file.folder_name = self.dev_conf.file.folder_name + "/"  

        if not (os.path.isdir(self.dev_conf.file.file_path+self.dev_conf.file.folder_name)):
            os.mkdir(self.dev_conf.file.file_path+self.dev_conf.file.folder_name)
            # logging.debug(f'Folder name does not exist, creating')

        if not (self.dev_conf.file.file_name[-5:] == ".hdf5"):
            self.dev_conf.file.file_name = self.dev_conf.file.file_name + ".hdf5"

        self.dev_conf.file.curr_file_name = (self.dev_conf.file.file_path + self.dev_conf.file.folder_name + self.dev_conf.file.file_name)
        # logging.debug(f'Full file path: {self.dev_conf.file.curr_file_name}')

        try:
            with h5py.File((self.dev_conf.file.curr_file_name), 'w') as f:
                metadata_group = f.create_group('metadata')
                for key, value in metadata.items():
                    metadata_group.attrs[key] = value
            
                for c, b in zip(self.buffer_manager.active_channels, self.buffer_manager.np_channel_arrays):
                    f.create_dataset(('adc_counts_'+str(c)), data = b)
                    # logging.debug(f'Creating dataset: adc_counts_{str(c)} with data : {b}')

                for channel in self.buffer_manager.active_channels:
                    p = [self.buffer_manager.bin_edges, self.buffer_manager.pha_counts[channel]]
                    # Create a dataset in the already existing file to contain the PHA data
                    f.create_dataset(('pha_'+str(channel)), data = p)
                f.create_dataset('trigger_timings', data=self.buffer_manager.trigger_times)
        except Exception as e: 
            logging.debug(f'Exception caught:{e}')
            self.dev_conf.file.last_write_success = False
            return

        self.pico_status.flags.system_state = "Connected to Picoscope, hdf5 file written"
        # logging.debug(f'File writing finished successfully')
        self.dev_conf.file.last_write_success = True
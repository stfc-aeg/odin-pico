"""File to create a h5py file, and then add the capture data to it."""

import logging
import os
from dataclasses import asdict
import h5py
from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus
from odin_pico.pico_util import PicoUtil


class FileWriter:
    """Class that represents data in a h5py file."""

    def __init__(
        self,
        dev_conf=DeviceConfig(),
        buffer_manager=BufferManager(),
        pico_status=DeviceStatus(),
    ):
        """Initialise the FileWriter Class."""
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager
        self.pico_status = pico_status
        self.util = PicoUtil()
        self.capture_number = 1
        self.file_error = False

    def check_file_name(self):
        """Identify and check the file path before collecting data."""
        # Check whether file name is empty, or file already exists

        if self.dev_conf.file.file_name == "":
            return False

        if self.dev_conf.file.file_name[-5:] == ".hdf5":
            if os.path.isfile(self.dev_conf.file.file_path
                              + self.dev_conf.file.folder_name
                              + self.dev_conf.file.file_name
                              ) or os.path.isfile(self.dev_conf.file.file_path
                                                  + self.dev_conf.file.folder_name
                                                  + self.dev_conf.file.file_name[-5:]
                                                  + "_1.hdf5"):
                return False

        else:
            if os.path.isfile(self.dev_conf.file.file_path
                              + self.dev_conf.file.folder_name
                              + self.dev_conf.file.file_name
                              + ".hdf5") or os.path.isfile(self.dev_conf.file.file_path
                                                           + self.dev_conf.file.folder_name
                                                           + self.dev_conf.file.file_name
                                                           + "_1.hdf5"):
                return False

        # Check if file is missing '.hdf5' at the end
        if not (self.dev_conf.file.file_name[-5:] == ".hdf5"):
            self.dev_conf.file.file_name = self.dev_conf.file.file_name + ".hdf5"

        # Check if folder name is valid
        if (
            self.dev_conf.file.folder_name != ""
            and self.dev_conf.file.folder_name[-1:] != "/"
        ):
            self.dev_conf.file.folder_name = self.dev_conf.file.folder_name + "/"

        # Makes a new directory if it does not already exist
        logging.debug(f"file_path:{self.dev_conf.file.file_path}")
        if not (
            os.path.isdir(self.dev_conf.file.file_path + self.dev_conf.file.folder_name)
        ):
            os.mkdir(self.dev_conf.file.file_path + self.dev_conf.file.folder_name)

        return True

    def write_hdf5(self):
        """Create and write to a hdf5 file."""
        metadata = self.util.flatten_metadata_dict(
            {
                "active_channels": self.buffer_manager.active_channels[:],
                "channel_a": self.dev_conf.channel_a.custom_asdict(),
                "channel_b": self.dev_conf.channel_b.custom_asdict(),
                "channel_c": self.dev_conf.channel_c.custom_asdict(),
                "channel_d": self.dev_conf.channel_d.custom_asdict(),
                "trigger": self.dev_conf.trigger.custom_asdict(),
                "resolution": self.dev_conf.mode.resolution,
                "timebase": self.dev_conf.mode.timebase,
            }
        )
        
        # Update system state, and keep track of previous system state
        old_system_state = self.pico_status.flags.system_state
        self.pico_status.flags.system_state = "Captures Collected, Writing HDF5 File"

        # Change file name depending on how many times capture has been run
        if self.dev_conf.capture.capture_repeat:

            if self.capture_number == 1:
                self.dev_conf.file.file_name = self.dev_conf.file.file_name[:-5]
                self.dev_conf.file.file_name = self.dev_conf.file.file_name + "_" + (
                    str(self.capture_number) + ".hdf5")
            else:
                self.dev_conf.file.file_name = self.dev_conf.file.file_name[:-6]
                self.dev_conf.file.file_name = self.dev_conf.file.file_name + (
                    str(self.capture_number) + ".hdf5")

        # Take note of file path so it can be written to
        self.dev_conf.file.curr_file_name = (
            self.dev_conf.file.file_path
            + self.dev_conf.file.folder_name
            + self.dev_conf.file.file_name
        )

        try:
            with h5py.File((self.dev_conf.file.curr_file_name), "w") as f:
                metadata_group = f.create_group("metadata")
                for key, value in metadata.items():
                    metadata_group.attrs[key] = value

                # Add the collected data to the created file
                for c, b in zip(
                    self.buffer_manager.active_channels,
                    self.buffer_manager.np_channel_arrays,
                ):
                    f.create_dataset(("adc_counts_" + str(c)), data=b)

                for channel in self.buffer_manager.active_channels:
                    p = [
                        self.buffer_manager.bin_edges,
                        self.buffer_manager.pha_counts[channel],
                    ]
                    # Create a dataset in the already existing file to contain the PHA data
                    f.create_dataset(("pha_" + str(channel)), data=p)
                f.create_dataset(
                    "trigger_timings", data=self.buffer_manager.trigger_times
                )
        except Exception as e:
            logging.debug(f"Exception caught:{e}")
            self.dev_conf.file.last_write_success = False
            return

        # Remove '_x' from file name if last capture in acquisition group
        if self.dev_conf.capture.capture_repeat:
            if self.capture_number == self.dev_conf.capture.repeat_amount:
                self.dev_conf.file.file_name = self.dev_conf.file.file_name[:-7]

        self.capture_number += 1
        self.dev_conf.file.last_write_success = True
        self.pico_status.flags.system_state = old_system_state

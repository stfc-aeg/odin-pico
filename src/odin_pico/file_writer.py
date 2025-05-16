"""Create an HDF5 file and write capture data for both normal and
time-based acquisitions.
"""

import logging
import math
import os

import h5py
import numpy as np

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus
from odin_pico.pico_util import PicoUtil


class FileWriter:
    """Represent capture data in an HDF5 file."""

    def __init__(
        self,
        dev_conf: DeviceConfig = DeviceConfig(),
        buffer_manager: BufferManager = BufferManager(),
        pico_status: DeviceStatus = DeviceStatus(),
    ):
        self.dev_conf = dev_conf
        self.buffer_manager = buffer_manager
        self.pico_status = pico_status
        self.util = PicoUtil()
        self.capture_number = 1
        self.file_error = False

    def check_file_name(self) -> bool:
        """Check file name settings are valid, return True when a new file can safely be created."""

        if self.dev_conf.file.file_name == "":
            return False

        # ensure ".hdf5" extension
        if not self.dev_conf.file.file_name.endswith(".hdf5"):
            self.dev_conf.file.file_name += ".hdf5"

        # ensure folder ends with "/"
        if self.dev_conf.file.folder_name and \
           not self.dev_conf.file.folder_name.endswith("/"):
            self.dev_conf.file.folder_name += "/"

        full_path = (
            self.dev_conf.file.file_path +
            self.dev_conf.file.folder_name +
            self.dev_conf.file.file_name
        )

        root, ext = os.path.splitext(full_path)
        if os.path.isfile(full_path) or os.path.isfile(f"{root}_1{ext}"):
            return False

        # Create folder if missing
        os.makedirs(
            self.dev_conf.file.file_path + self.dev_conf.file.folder_name,
            exist_ok=True,
        )
        return True

    def write_hdf5(self, write_accumulated: bool = False):
        """
        Create and write to a hdf5 file.
        ----------
        write_accumulated
            False - normal capture of N waveforms.
            True  - time-based capture.
        """
        # build metadata dictionary from channel informaiton
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
        self.pico_status.flags.system_state = "Captures Collected, Creating HDF5 File"

        # Change file name depending on how many times capture has been run
        if self.dev_conf.capture.capture_repeat:
            if self.capture_number == 1:
                name = self.dev_conf.file.file_name[:-5] # strip .hdf5
            else:
                name = self.dev_conf.file.file_name[:-7] # strip _n.hdf5
            self.dev_conf.file.file_name = f"{name}_{self.capture_number}.hdf5"

        # Take note of file path so it can be written to
        self.dev_conf.file.curr_file_name = (
            self.dev_conf.file.file_path +
            self.dev_conf.file.folder_name +
            self.dev_conf.file.file_name
        )
        fname = self.dev_conf.file.curr_file_name
        logging.debug(f"writing to {fname}")


        try:
            with h5py.File(fname, "w") as f:

                # Create metadata group
                meta = f.create_group("metadata")
                for k, v in metadata.items():
                    meta.attrs[k] = v

                if hasattr(self.buffer_manager, "temp_set_last"):
                    meta.attrs["tec_set_C"] = self.buffer_manager.temp_set_last
                if hasattr(self.buffer_manager, "temp_meas_last"):
                    meta.attrs["tec_meas_C"] = self.buffer_manager.temp_meas_last

                if write_accumulated and self.buffer_manager.capture_blocks:

                    capture_blocks  = self.buffer_manager.capture_blocks
                    trigger_blocks  = self.buffer_manager.trigger_blocks
                    samples_per_cap = capture_blocks[0][0].shape[1]
                    total_captures  = sum(block[0].shape[0] for block in capture_blocks)

                    # Create per-channel datasets
                    channel_datasets = {
                        ch_id: f.create_dataset(
                            f"adc_counts_{ch_id}",
                            shape   =(total_captures, samples_per_cap),
                            dtype   =capture_blocks[0][0].dtype
                        )
                        for ch_id in self.buffer_manager.active_channels
                    }

                    # Create trigger_timing datasets
                    trig_dataset = f.create_dataset(
                        "trigger_timings",
                        shape =(total_captures,),
                        dtype =trigger_blocks[0].dtype
                    )
                    # copy each capture block into its position in the dataset
                    next_row = 0  # offset for position in the dataset

                    for blk_idx, block in enumerate(capture_blocks):
                        seg_caps = block[0].shape[0]  # rows in this block
                        row_slice = slice(next_row, next_row + seg_caps) # Slice the block if captures_completed < size of array

                        # write capture for every active channel
                        for chan_arr, ch_id in zip(block, self.buffer_manager.active_channels):
                            channel_datasets[ch_id][row_slice] = chan_arr

                        # write corresponding trigger intervals
                        trig_dataset[row_slice] = trigger_blocks[blk_idx]

                        self.pico_status.flags.system_state = (
                            f"Writing HDF5 File: Writing Captures: {math.trunc((row_slice.stop/total_captures)*100)}% completed")
                        logging.debug(
                            f"Writing HDF5 File: Writing Captures {row_slice.start+1}–{row_slice.stop} out of {total_captures}")
                        next_row += seg_caps
                        
                ## File writing for N captures
                else:
                    source = self.buffer_manager.np_channel_arrays
                    trigger_times = self.buffer_manager.trigger_times

                    for ch_id, data in zip(self.buffer_manager.active_channels, source):
                        logging.debug(f"[HDF5] adc_counts_{ch_id} : {data.shape[0]} captures")
                        f.create_dataset(f"adc_counts_{ch_id}", data=data)

                    f.create_dataset("trigger_timings", data=trigger_times)

                # PHA datasets 
                edges = self.buffer_manager.bin_edges
                for ch_id in self.buffer_manager.active_channels:
                    counts = self.buffer_manager.pha_counts[ch_id]
                    if edges and counts and len(edges) == len(counts):
                        f.create_dataset(f"pha_{ch_id}", data=[edges, counts])

            self.dev_conf.file.last_write_success = True

        except Exception as e:
            logging.debug(f"Exception while writing HDF5: {e}")
            self.dev_conf.file.last_write_success = False
            return

        # 4)  ------ reset capture-repeat suffix if finished ---------
        if self.dev_conf.capture.capture_repeat and \
           self.capture_number == self.dev_conf.capture.repeat_amount:
            self.dev_conf.file.file_name = self.dev_conf.file.file_name[:-7]

        self.capture_number += 1
        self.dev_conf.file.last_write_success = True

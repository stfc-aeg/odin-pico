import time
import json
from pathlib import Path
import logging
import math
import os

import h5py
import numpy as np

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.pico_config import DeviceConfig
from odin_pico.DataClasses.pico_status import DeviceStatus
from odin_pico.Utilities.pico_util import PicoUtil


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
        self.file_error = False

    def check_file_name(self) -> bool:
        """Check file name settings are valid, return True when a new file can safely be created."""

        if self.dev_conf.file.file_name == "":
            return False

        # ensure ".hdf5" extension
        if not self.dev_conf.file.file_name.endswith(".hdf5"):
            self.dev_conf.file.file_name += ".hdf5"

        # ensure folder ends with "/"
        if (self.dev_conf.file.folder_name
                and not self.dev_conf.file.folder_name.endswith("/")):
            self.dev_conf.file.folder_name += "/"

        full_path = (
            self.dev_conf.file.file_path +
            self.dev_conf.file.folder_name +
            self._build_filename()
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
    
    def _build_filename(self):
        """
        create <base><temp><repeat>.hdf5
        """
        base = self.dev_conf.file.file_name
        if base.endswith(".hdf5"):
            base = base[:-5]

        if self.dev_conf.file.temp_suffix:
            base += self.dev_conf.file.temp_suffix
        if self.dev_conf.file.repeat_suffix:
            base += self.dev_conf.file.repeat_suffix
        return base + ".hdf5"

    def calculate_estimated_filesize(
        self,
        total_captures: int,
        samples_per_cap: int,
        adc_dtype: np.dtype,
        trigger_dtype: np.dtype,
        pha_bin_count: int,
        pha_dtype: np.dtype,
        num_waveform_channels: int, # Correctly uses toggled waveform channel count
        num_pha_channels: int       # Correctly uses toggled PHA channel count
    ) -> float:
        """Estimates the HDF5 filesize in megabytes (MB) based on toggled datasets."""

        # Calculate size of ADC data based on the number of channels with waveforms toggled
        adc_bytes = total_captures * samples_per_cap * num_waveform_channels * adc_dtype.itemsize

        # Trigger data is only saved if waveform data is present
        trigger_bytes = 0
        if num_waveform_channels > 0:
            trigger_bytes = total_captures * trigger_dtype.itemsize

        # Calculate size of PHA data based on the number of channels with PHA toggled
        pha_bytes = 0
        if pha_bin_count > 0 and pha_dtype is not None and num_pha_channels > 0:
            # For each channel, data is stored as [edges, counts], which becomes a (2, N) array
            # So, the number of elements is (len(edges) + len(counts))
            pha_bytes = (pha_bin_count + pha_bin_count) * num_pha_channels * pha_dtype.itemsize

        total_bytes = adc_bytes + trigger_bytes + pha_bytes
        
        # Convert bytes to megabytes
        logging.debug(total_bytes)
        logging.debug(adc_bytes)
        logging.debug(trigger_bytes)
        logging.debug(pha_bytes)
        logging.debug("")
        logging.debug("")

        logging.debug(pha_bin_count)
        logging.debug(pha_dtype)
        logging.debug(num_pha_channels)
        total_mb = total_bytes / (1024**2)
        
        return total_mb

    def write_hdf5(self, write_accumulated: bool = False):
        """
        Create and write to a hdf5 file.
        ----------
        write_accumulated
            False - normal capture of N waveforms.
            True  - time-based capture.
        """
        if write_accumulated and self.buffer_manager.capture_blocks:
            # Parameters for time-based capture
            capture_blocks = self.buffer_manager.capture_blocks
            trigger_blocks = self.buffer_manager.trigger_blocks
            total_captures = sum(block[0].shape[0] for block in capture_blocks)
            samples_per_cap = capture_blocks[0][0].shape[1]
            adc_dtype = capture_blocks[0][0].dtype
            trigger_dtype = trigger_blocks[0].dtype
        else:
            # Parameters for normal N-capture
            source = self.buffer_manager.np_channel_arrays
            if not source:
                logging.error("No data in buffer to write.")
                return
            total_captures = source[0].shape[0]
            samples_per_cap = source[0].shape[1]
            adc_dtype = source[0].dtype
            
            if self.buffer_manager.trigger_times:
                trigger_dtype = np.array(self.buffer_manager.trigger_times).dtype
            else:
                trigger_dtype = np.dtype('int64') 

        # This parameter is no longer needed as we now use specific channel counts
        # num_channels = len(self.buffer_manager.active_channels)

        # Include PHA data in the estimate if it exists
        pha_bin_count = len(self.buffer_manager.bin_edges)
        
        # This logic is now inside the JSON section to ensure it's up to date
        # if self.buffer_manager.pha_counts.size > 0:
        #     pha_dtype = self.buffer_manager.pha_counts.dtype
        # else:
        #     pha_dtype = None

        # This call is moved to after the file write to use the most current data
        # actual_filesize_mb = self.calculate_estimated_filesize(...)
        
        start_time = time.perf_counter()

        # build metadata dictionary from channel information
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

        channel_key = {
            0: "channel_a",
            1: "channel_b",
            2: "channel_c",
            3: "channel_d",
        }
        
        pha_toggled_channels = [
            chan for chan in self.buffer_manager.active_channels
            if getattr(self.dev_conf, channel_key[chan]).PHAToggled
        ]
        waveform_toggled_channels = [
            chan for chan in self.buffer_manager.active_channels
            if getattr(self.dev_conf, channel_key[chan]).waveformsToggled
        ]

        fname = (
                self.dev_conf.file.file_path
                + self.dev_conf.file.folder_name
                + self._build_filename()
                )
        self.dev_conf.file.curr_file_name = fname
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
                        if ch_id in waveform_toggled_channels
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
                            if ch_id in waveform_toggled_channels:
                                channel_datasets[ch_id][row_slice] = chan_arr

                        # write corresponding trigger intervals
                        trig_dataset[row_slice] = trigger_blocks[blk_idx]

                        self.pico_status.flags.system_state = (
                            f"Writing HDF5 File: Writing Captures: {math.trunc((row_slice.stop/total_captures)*100)}% completed")
                        logging.debug(
                            f"Writing HDF5 File: Writing Captures {row_slice.start+1}-{row_slice.stop} out of {total_captures}")
                        next_row += seg_caps
                        
                ## File writing for N captures
                else:
                    source = self.buffer_manager.np_channel_arrays
                    trigger_times = self.buffer_manager.trigger_times

                    for ch_id, data in zip(self.buffer_manager.active_channels, source):
                        if ch_id in waveform_toggled_channels:
                            logging.debug(f"[HDF5] adc_counts_{ch_id} : {data.shape[0]} captures")
                            f.create_dataset(f"adc_counts_{ch_id}", data=data)

                    f.create_dataset("trigger_timings", data=trigger_times)

                # PHA datasets 
                edges = self.buffer_manager.bin_edges
                for ch_id in self.buffer_manager.active_channels:
                    if ch_id in pha_toggled_channels:
                        counts = self.buffer_manager.pha_counts[ch_id]
                        if len(edges) > 0 and len(edges) == len(counts):
                            f.create_dataset(f"pha_{ch_id}", data=[edges, counts])
                        
            self.dev_conf.file.last_write_success = True

        except Exception as e:
            logging.debug(f"Exception while writing HDF5: {e}")
            self.dev_conf.file.last_write_success = False
            return

        self.dev_conf.file.last_write_success = True

        #########################################

        elapsed_time = time.perf_counter() - start_time
        logging.info(f"HDF5 file written in {elapsed_time:.6f} seconds")

        # --- Get parameters for accurate size calculation ---
        edges = self.buffer_manager.bin_edges
        sample_pha_counts = np.array([])
        if pha_toggled_channels and isinstance(self.buffer_manager.pha_counts, dict):
            sample_pha_counts = self.buffer_manager.pha_counts.get(pha_toggled_channels[0], np.array([]))
        pha_dtype = sample_pha_counts.dtype if hasattr(sample_pha_counts, 'dtype') else None

        actual_filesize_mb = self.calculate_estimated_filesize(
            total_captures=total_captures,
            samples_per_cap=samples_per_cap,
            adc_dtype=adc_dtype,
            trigger_dtype=trigger_dtype,
            pha_bin_count=pha_bin_count,
            pha_dtype=pha_dtype,
            num_waveform_channels=len(waveform_toggled_channels),
            num_pha_channels=len(pha_toggled_channels)
        )

        # --- JSON Filename Parsing ---
        json_path = Path("file_data.json")
        basename = Path(fname).stem
        parts = basename.split('_')
        
        # Check if the last part of the name is a number (the repeat counter)
        if len(parts) > 1 and parts[-1].isdigit():
            # Join all parts except the last one to create the key for grouping runs
            fname_key = "_".join(parts[:-1])
        else:
            # Otherwise, use the whole basename as the key
            fname_key = basename
        
        # --- JSON Logging (with comprehensive averages) ---
        results = {}
        if json_path.exists():
            try:
                with open(json_path, "r") as jf:
                    results = json.load(jf)
            except Exception as e:
                logging.warning(f"Could not read JSON log: {e}")

        # Get or initialise the entry for this configuration
        data = results.get(fname_key, {
            "elapsed_times_s": [], "file_sizes_mb": [], "capture_counts": [],
            "averages": {}
        })

        # Append data from the current run
        data["elapsed_times_s"].append(elapsed_time)
        data["file_sizes_mb"].append(actual_filesize_mb)
        data["capture_counts"].append(total_captures)

        # Recalculate all averages
        times, sizes, caps = data["elapsed_times_s"], data["file_sizes_mb"], data["capture_counts"]
        run_count = len(times)
        sum_times, sum_sizes, sum_caps = sum(times), sum(sizes), sum(caps)

        avg_data = data["averages"]
        avg_data["run_count"] = run_count
        avg_data["avg_elapsed_time_s"] = sum_times / run_count
        avg_data["avg_file_size_mb"] = sum_sizes / run_count
        # True average rates (total data / total time)
        avg_data["avg_capture_rate_cps"] = sum_caps / sum_times if sum_times > 0 else 0
        avg_data["avg_write_speed_mbps"] = sum_sizes / sum_times if sum_times > 0 else 0
        
        # Update the main dictionary and write to file
        results[fname_key] = data
        with open(json_path, "w") as jf:
            json.dump(results, jf, indent=4)
        
        logging.info(f"Successfully logged results for {fname_key} to {json_path}")

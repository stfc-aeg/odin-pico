"""Buffer manager which prepares and accepts buffers for the PicoScope."""

import ctypes
import logging
from collections import deque
from typing import List
import numpy as np
from odin_pico.DataClasses.pico_config import DeviceConfig
from odin_pico.Utilities.pico_util import PicoUtil
import psutil
import math

class BufferManager:
    """Class which manages the buffers that are filled with data by the PicoScope."""

    def __init__(self, dev_conf=DeviceConfig()):
        """Initialise the BufferManager Class."""
        self.dev_conf = dev_conf
        self.util = PicoUtil()
        self.channels = [
            getattr(self.dev_conf, f"channel_{name}")
            for name in self.dev_conf.channel_names
        ]

        self.active_channels = []
        self.overflow = None
        self.np_channel_arrays = []
        self.trigger_times = []
        self.capture_blocks: List[List[np.ndarray]] = []
        self.trigger_blocks:  List[np.ndarray]   = []
        self.trigger_intervals = deque(maxlen=500)

        self.lv_channel_arrays = []
        self.lv_channels_active = []

        self.pha_channels_active = [False] * 4
        self.pha_active_channels = []
        self.bin_edges = []
        self.pha_counts = np.zeros((len(self.dev_conf.channel_names), 
                                    self.dev_conf.pha.num_bins), dtype=np.int64)
        self.bin_edges = np.zeros(self.dev_conf.pha.num_bins, dtype=np.float64)

    def estimate_max_time(self):
        """
        Return estimated seconds of acquisition that can still fit into RAM,
        or 0 if avg trigger times unavailable.
        """
        if self.avg_trigger_dt() is None:
            return 0

        n_chan = len(self.active_channels) or 1
        samples_per_cap = (
            self.dev_conf.capture.pre_trig_samples +
            self.dev_conf.capture.post_trig_samples
        )
        capture_dur  = samples_per_cap * self.dev_conf.mode.samp_time
        bytes_per_cap = samples_per_cap * 2 * n_chan

        # allowing for reserving 25% of current free memmory
        allowed = psutil.virtual_memory().available * 0.75
        if bytes_per_cap == 0 or bytes_per_cap > allowed:
            return 0

        max_caps = allowed // bytes_per_cap
        return math.trunc(max_caps * (capture_dur + self.avg_trigger_dt()))

    def add_trigger_intervals(self, deltas):
        """Append trigger timing values to the deque."""
        if deltas is None or len(deltas) == 0:
            return
        # skip first element of trigger intervals, from looking at trigger data, it seems to be inaccurate
        self.trigger_intervals.extend(deltas[1:] if len(deltas) > 1 else deltas)
        
    def avg_trigger_dt(self):
        """Mean of stored intervals; returns 0 if deque empty."""
        if not self.trigger_intervals:
            return 0
        return sum(self.trigger_intervals) / len(self.trigger_intervals)

    def generate_arrays(self, *args):
        """Create the buffers that the picoscope will be mapped onto for data collection."""
        self.clear_arrays()
        self.check_channels()
        if args:
            n_captures = args[0]
        else:
            n_captures = self.dev_conf.capture.n_captures
        
        self.overflow = (ctypes.c_int16 * n_captures)()
        samples = (self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples)

        for i in range(len(self.active_channels)):
            #logging.debug(f"Creating array for channel for {i}")
            self.np_channel_arrays.append(np.zeros(shape=(n_captures, samples), dtype=np.int16))

    def accumulate_pha(self, chan, counts):
        """Add the new PHA data to the previous data, if there is any data."""
        # create references to bin_edges and counts for this channels pha

        self.pha_counts[chan] += counts

        # logging.debug(f"pha arrays shape: {self.pha_arrays}")
        # bin_edges, counts = self.pha_arrays[pha_idx]
        # # store bin_edges
        # self.bin_edges = bin_edges

        # self.pha
            
        #     #self.

        # current_pha_data = (self.pha_arrays[pha_idx]).tolist()
        # self.bin_edges = current_pha_data[0]
        # pha_counts = (current_pha_data)[1]

        # # Adds PHA to previous data, unless there is no previous data
        # if len(self.pha_counts[chan]) != 0:
        #     self.pha_counts[chan] = np.array(pha_counts) + np.array(
        #         self.pha_counts[chan]
        #     )
        #     self.pha_counts[chan] = self.pha_counts[chan].tolist()
        # else:
        #     self.pha_counts[chan] = pha_counts

    def check_channels(self):
        """Check which channels are active, LV active and PHA active."""
        self.active_channels.clear()
        for chan in self.channels:
            if chan.active:
                self.active_channels.append(chan.channel_id)
                if chan.live_view:
                    self.lv_channels_active.append(chan.channel_id)
                if chan.pha_active:
                    self.pha_channels_active[chan.channel_id] = True
                    self.pha_active_channels.append(chan.channel_id)

    def save_lv_data(self, time_based):
        """Return a live view of traces being captured."""
        self.lv_channel_arrays = []

        for c, b in zip(self.active_channels, self.np_channel_arrays):
            # Find current data, along with channel range and offset
            if time_based:
                array = b[-1]
            else:
                array = b[(self.dev_conf.capture_run.caps_in_run - 1)]

            values = self.util.adc2mV(
                array,
                self.channels[c].range,
                self.dev_conf.meta_data.max_adc,
            ).tolist()
            if self.channels[c].live_view:
                self.lv_channel_arrays.append(values)

    def create_tb_block(self, caps_in_run: int) -> int:
        """
        Allocate one NumPy buffer per active channel and append it to
        capture_blocks. Assigns np_channel_arrays to the blocks so that assign_memory
        in picodevice can pick up these arrays without changes. 
        """
        self.check_channels()
        samples_per_cap = (
            self.dev_conf.capture.pre_trig_samples +
            self.dev_conf.capture.post_trig_samples
        )

        block = [
            np.zeros((caps_in_run, samples_per_cap), dtype=np.int16)
            for _ in self.active_channels
        ]
        self.capture_blocks.append(block)
        self.trigger_blocks.append(np.zeros(caps_in_run, dtype=np.float64))

        # reference to the newly created block to use in funcitons that expect data to be 
        # accessible in self.np_channel_arrays
        self.np_channel_arrays = block

        self.overflow = (ctypes.c_int16 * caps_in_run)()

        return len(self.capture_blocks) - 1

    def slice_block_to_valid(self, block_idx: int, seg_caps: int):
        """
        After a rapid-block run finishes with `seg_caps < caps_in_run`,
        discard the never-filled tail rows for every channel and the
        corresponding trigger-time array.
        """
        if seg_caps == self.capture_blocks[block_idx][0].shape[0]:
            return

        for ch in range(len(self.active_channels)):
            self.capture_blocks[block_idx][ch] = \
                self.capture_blocks[block_idx][ch][:seg_caps]

        self.trigger_blocks[block_idx] = \
            self.trigger_blocks[block_idx][:seg_caps]

    def clear_arrays(self):
        """Remove previously created buffers from the buffer_manager."""
        arrays = [
            self.active_channels,
            self.trigger_times,
            self.np_channel_arrays,
            self.lv_channels_active,
            self.pha_active_channels
        ]
        for array in arrays:
            array.clear()
        self.capture_blocks: List[List[np.ndarray]] = []
        self.trigger_blocks:  List[np.ndarray]   = []
        self.pha_channels_active = [False] * 4

    def reset_pha(self):
        """Reset PHA counts array based on current channel count and bin settings."""
        self.pha_counts = np.zeros(
            (len(self.dev_conf.channel_names), self.dev_conf.pha.num_bins), 
            dtype=np.int64
        )
        self.bin_edges = np.zeros(self.dev_conf.pha.num_bins, dtype=np.float64)
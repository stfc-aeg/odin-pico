"""Manage the PicoScope in preparing for, and extracting the data."""

import ctypes
import logging
import math
import psutil
import sys
import time

from picosdk.functions import mV2adc
from picosdk.ps5000a import ps5000a as ps

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.pico_config import DeviceConfig
from odin_pico.DataClasses.pico_status import DeviceStatus
from odin_pico.Utilities.pico_util import PicoUtil
from odin_pico.PS5000A_Trigger_Info import Trigger_Info
from odin_pico.file_writer import FileWriter
from odin_pico.analysis import PicoAnalysis
from odin_pico.DataClasses.gpio_config import GPIOConfig

class PicoDevice:
    """Class that communicates with the scope to collect data."""

    def __init__(
        self, disk, dev_conf=DeviceConfig(), pico_status=DeviceStatus(),
        buffer_manager=BufferManager(), analysis=PicoAnalysis(),
        file_writer=None, gpio_config=GPIOConfig()
    ):
        """Initialise the PicoDevice class."""
        self.util = PicoUtil()
        self.dev_conf = dev_conf
        self.pico_status = pico_status
        self.buffer_manager = buffer_manager
        self.file_writer = file_writer or FileWriter(disk)
        self.analysis = analysis
        self.gpio_config = gpio_config
        
        self.channels = [
            getattr(self.dev_conf, f"channel_{name}")
            for name in self.dev_conf.channel_names
        ]

        self._tb_current_block = None
        self.seg_caps = 0
        self.prev_seg_caps = 0
        self.elapsed_time = 0.0
        self.rec_caps = 0
        self.rec_time = 0

    def open_unit(self):
        """Initalise connection with the picoscope, and settings the status values."""
        # Open the PicoScope
        self.pico_status.open_unit = ps.ps5000aOpenUnit(
            ctypes.byref(self.dev_conf.mode.handle), None, self.dev_conf.mode.resolution
        )

        # Set maximum values
        if self.pico_status.open_unit == 0:
            ps.ps5000aMaximumValue(
                self.dev_conf.mode.handle, ctypes.byref(self.dev_conf.meta_data.max_adc)
            )
        else:
            self.pico_status.flags.system_state = "Failed to Connect"

        if self.dev_conf.pha.upper_range == 0:
            self.dev_conf.pha.upper_range = self.dev_conf.meta_data.max_adc.value

    def assign_pico_memory(self):
        """Give PicoScope memory locations for data to be extracted.

        Map the local buffers in the buffer_manager to the picoscope for
        each individual trace to be captured on each channel by the picoscope.
        """

        ps.ps5000aStop(self.dev_conf.mode.handle)
        # Set the number of memory segments to be used
        n_captures = self.dev_conf.capture_run.caps_in_run
        ps.ps5000aMemorySegments(
            self.dev_conf.mode.handle,
            n_captures,
            ctypes.byref(self.dev_conf.meta_data.samples_per_seg),
        )

        # Set the number of captures to be requested
        ps.ps5000aSetNoOfCaptures(self.dev_conf.mode.handle, n_captures)
        samples = (
            self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples
        )

        # Assign data buffers for the PicoScope to write to
        for c, b in zip(
            self.buffer_manager.active_channels,
            self.buffer_manager.np_channel_arrays,
        ):
            for i in range(self.dev_conf.capture_run.caps_comp, 
                           (self.dev_conf.capture_run.caps_comp + self.dev_conf.capture_run.caps_in_run)):
                buff = b[i]
                ps.ps5000aSetDataBuffer(
                    self.dev_conf.mode.handle,
                    c,
                    buff.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                    samples,
                    i - self.dev_conf.capture_run.caps_comp,
                    0,
                )

    def set_trigger(self):
        """Responsible for setting the trigger information on the picoscope."""
        # Find the channel ranges
        channel_range = next(
            (
                chan.range
                for chan in self.channels
                if chan.channel_id == self.dev_conf.trigger.source
            ),
            None,
        )

        # Find the trigger threshold
        threshold = int(
            mV2adc(
                self.dev_conf.trigger.threshold,
                channel_range,
                self.dev_conf.meta_data.max_adc,
            )
        )

        # Set up the trigger
        ps.ps5000aSetSimpleTrigger(
            self.dev_conf.mode.handle,
            self.dev_conf.trigger.active,
            self.dev_conf.trigger.source,
            threshold,
            self.dev_conf.trigger.direction,
            self.dev_conf.trigger.delay,
            self.dev_conf.trigger.auto_trigger_ms,
        )
        if self.pico_status.flags.user_capture:
            logging.debug(f"Trigger: {self.dev_conf.trigger.active}")

    def set_channels(self):
        """Set the channel information for each channel on the picoscope."""
        for chan in self.channels:
            max_v = ctypes.c_float(0)
            min_v = ctypes.c_float(0)
            ps.ps5000aGetAnalogueOffset(
                self.dev_conf.mode.handle,
                chan.range,
                chan.coupling,
                ctypes.byref(max_v),
                ctypes.byref(min_v),
            )
            
            offset = self.util.calc_offset(chan.range, chan.offset)
            ps.ps5000aSetChannel(
                self.dev_conf.mode.handle,
                chan.channel_id,
                int(chan.active),
                chan.coupling,
                chan.range,
                offset,
            )

    def run_setup(self, *args):
        """Responsible for "setting up" the picoscope.

        Call functions that apply local settings to the picoscope
        and for calling the buffer generating function.
        """
        # Open the scope if not already open
        if self.pico_status.open_unit != 0:
            self.open_unit()

        if self.pico_status.open_unit == 0:
            self.set_channels()
            self.set_trigger()

            if args:
                self.buffer_manager.generate_arrays(args[0])
            else:
                self.buffer_manager.generate_arrays()
            return True

    def run_tb_setup(self) -> bool:
        """
        Prepare the PicoScope for one rapid-block run (time-based mode).

        Returns
        -------
        bool
            True - block buffers were allocated and memory mapped  
            False - aborted early because the next block would exceed
                    25 % of currently-available system RAM.
        """
        # Calculate memory needed for the next block
        caps_in_run = self.dev_conf.capture_run.caps_in_run
        samples_per_cap = (
            self.dev_conf.capture.pre_trig_samples +
            self.dev_conf.capture.post_trig_samples
        )
        n_chan = len(self.buffer_manager.active_channels)
        bytes_new_block = samples_per_cap * 2 * caps_in_run * n_chan
        allowed = psutil.virtual_memory().available * 0.25

        if bytes_new_block > allowed:
            self.pico_status.flags.abort_cap = True
            return False

        if self.pico_status.open_unit != 0:
            self.open_unit()

        if self.pico_status.open_unit == 0:
            self.set_channels()
            self.set_trigger()

            # Allocate buffers for this run
            self._tb_current_block = self.buffer_manager.create_tb_block(caps_in_run)

            # Map the buffers
            self.assign_pico_memory()
            return True

    def run_block(self):
        """Complete a PicoScope capture run using the rapid block functions        

        Responsible for telling the picoscope how much data to collect and
        when to collect it, retrives that data into local buffers once
        data collection is finished.
        """
        self.prev_seg_caps = 0
        self.seg_caps = 0
        start_time = time.time()
        t = time.time()
        self.pico_status.block_ready = ctypes.c_int16(0)
        self.dev_conf.meta_data.total_cap_samples = (
            self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples
        )
        self.dev_conf.meta_data.max_samples = ctypes.c_int32(
            self.dev_conf.meta_data.total_cap_samples
        )
        if not self.file_writer.file_error:
            if not self.pico_status.flags.user_capture and not self.gpio_config.listening:
                self.pico_status.flags.system_state = "Collecting LV Data"
            elif self.pico_status.flags.user_capture:
                self.pico_status.flags.system_state = "N capture collection"
            elif self.gpio_config.capture:
                self.pico_status.flags.system_state = f"Completing capture: {self.gpio_config.gpio_captures}"

        ps.ps5000aRunBlock(
            self.dev_conf.mode.handle,
            self.dev_conf.capture.pre_trig_samples,
            self.dev_conf.capture.post_trig_samples,
            self.dev_conf.mode.timebase,
            None,
            0,
            None,
            None,
        )

        current_system_state = self.pico_status.flags.system_state

        collect = True
        # Waits until the scope has finished collecting all of the captures
        while (
            self.pico_status.block_ready.value == self.pico_status.block_check.value and
            collect
        ):
            ps.ps5000aIsReady(
                self.dev_conf.mode.handle,
                ctypes.byref(self.pico_status.block_ready),
            )

            if time.time() - t >= 2.5:
                if self.seg_caps == 0:
                    self.pico_status.flags.system_state = "Waiting for Trigger"
                    t = time.time()
                
            if (time.time() - start_time) > 10:
                if self.seg_caps == 0:
                    logging.debug("Aborting due to waiting for over 10s for trigger")
                    self.pico_status.flags.abort_cap = True
                    collect = False

            # Stop scope if user chooses to abort capture
            if self.pico_status.flags.abort_cap:
                ps.ps5000aStop(self.dev_conf.mode.handle)
                collect = False

            time.sleep(0.05)
            self.get_cap_count()
            self.prev_seg_caps = self.seg_caps

        self.pico_status.flags.system_state = current_system_state
        self.get_cap_count()

        if self.pico_status.flags.abort_cap:
            seg_to_indx = self.seg_caps
        else:
            seg_to_indx = self.dev_conf.capture_run.caps_in_run - 1

        # Retrive the captures that have been collected

        if not self.pico_status.flags.abort_cap:
            ps.ps5000aGetValuesBulk(
                self.dev_conf.mode.handle,
                ctypes.byref(self.dev_conf.meta_data.max_samples),
                0,
                (seg_to_indx),
                0,
                0,
                ctypes.byref(self.buffer_manager.overflow),
            )
            self.get_trigger_timing()
            
    def run_time_based_capture(self, total_time: float):
        """
        Repeated rapid-block acquisitions for a user-specified duration.
        Accumulates PHA and trigger info across the whole run.
        """
        self.buffer_manager.clear_arrays()

        start_time     = time.time()
        self.elapsed_time = 0.0
        block_running  = False
        self.prev_seg_caps = 0
        self.seg_caps      = 0

        self.dev_conf.meta_data.total_cap_samples = (
            self.dev_conf.capture.pre_trig_samples +
            self.dev_conf.capture.post_trig_samples
        )
        self.dev_conf.meta_data.max_samples = ctypes.c_int32(
            self.dev_conf.meta_data.total_cap_samples
        )
        self.pico_status.block_ready = ctypes.c_int16(0)

        while True:
            self.elapsed_time = time.time() - start_time
            if not self.gpio_config.listening:
                self.pico_status.flags.system_state = (
                    f"Time based collection")
            # User Aborted OR time limit reached
            if self.pico_status.flags.abort_cap or \
            (time.time() - start_time) >= total_time:
                if not self.pico_status.flags.abort_cap:
                    # Time limit reached, use abort mechanism
                    self.pico_status.flags.abort_cap = True
                if block_running:
                    # If block capture is running, stop the scope, get completed captures
                    self._tb_finish_captures()
                break

            # Start new capture block if one is not currently running
            if not block_running:
                # setup device for capture, allocate memory etc.
                if self.run_tb_setup(): 
                    # Begin capture if capture can fit into memory                    
                    self.pico_status.block_ready = ctypes.c_int16(0)
                    ps.ps5000aRunBlock(
                        self.dev_conf.mode.handle,
                        self.dev_conf.capture.pre_trig_samples,
                        self.dev_conf.capture.post_trig_samples,
                        self.dev_conf.mode.timebase,
                        None, 0, None, None
                    )
                    block_running    = True
                else:
                    # Do not start capture if running out of memory
                    block_running = False

            # Poll for data 
            else:
                ps.ps5000aIsReady(
                    self.dev_conf.mode.handle,
                    ctypes.byref(self.pico_status.block_ready)
                )
                # Data is ready to collect off the scope
                if (self.pico_status.block_ready.value !=
                        self.pico_status.block_check.value):

                    self._tb_finish_captures()
                    block_running = False

                # 10-s no-trigger 
                # else:
                #     if (time.time() - block_start_time) > 10:
                #         self.get_cap_count()
                #         if self.seg_caps == 0:
                #             logging.debug("Aborting due to 10s no trigger")
                #             self.pico_status.flags.abort_cap = True
                #             self._tb_finish_captures()
                #             break

            time.sleep(0.05)
        self.elapsed_time = 0.0

    def _accumulate_pha_for_block(self):
        """
        run analysis.pha_one_peak() for the current block by
        pretending caps_in_run == seg_caps, so the loop in pha_one_peak
        indexes only valid rows.
        """
        saved = self.dev_conf.capture_run.caps_in_run
        try:
            self.dev_conf.capture_run.caps_in_run = self.seg_caps
            self.analysis.pha_one_peak()
        finally:
            self.dev_conf.capture_run.caps_in_run = saved

    def _tb_finish_captures(self):
        """ Calls common functions needed when stopping scope
           and retrieving data """
        # Tell the scope to stop, retrieve number of completed captures, retrieve that many
        ps.ps5000aStop(self.dev_conf.mode.handle)
        self.get_cap_count()
        self._tb_get_values_and_triggers(self._tb_current_block)
        self._accumulate_pha_for_block()
        self.buffer_manager.slice_block_to_valid(self._tb_current_block, self.seg_caps)
        self._tb_unmap_block(self._tb_current_block)

    def _tb_get_values_and_triggers(self, block_idx: int):
        """
        Retrieve waveform data and trigger-time info for the *current* block
        after the scope has been stopped.  Uses self.seg_caps to know how many
        captures were actually completed.
        """
        if self.seg_caps == 0:
            return

        total_samples = (
            self.dev_conf.capture.pre_trig_samples +
            self.dev_conf.capture.post_trig_samples
        )
        max_samples = ctypes.c_int32(total_samples)

        ps.ps5000aGetValuesBulk(
            self.dev_conf.mode.handle,
            ctypes.byref(max_samples),
            0,       
            self.seg_caps - 1,
            0, 0,
            ctypes.byref(self.buffer_manager.overflow)
        )

        trig_info = (Trigger_Info * self.seg_caps)()
        ps.ps5000aGetTriggerInfoBulk(
            self.dev_conf.mode.handle,
            ctypes.byref(trig_info),
            0, self.seg_caps - 1
        )

        samp_time  = self.dev_conf.mode.samp_time
        trig_block = self.buffer_manager.trigger_blocks[block_idx]

        last_ctr = 0
        deltas   = []
        for i, info in enumerate(trig_info):
            delta_ctr = info.timeStampCounter - last_ctr
            trig_block[i] = delta_ctr * samp_time
            deltas.append(trig_block[i])
            last_ctr = info.timeStampCounter

        self.buffer_manager.add_trigger_intervals(deltas)

    def _tb_unmap_block(self, block_idx: int):
        """
        After a rapid-block run is finished and data have been copied,
        detach every segment pointer so the drivers internal table is reset.
        """
        caps_in_block = self.buffer_manager.capture_blocks[block_idx][0].shape[0]

        for ch_id in self.buffer_manager.active_channels:
            for seg in range(caps_in_block):
                # pass NULL to release the slot
                ps.ps5000aSetDataBuffer(
                    self.dev_conf.mode.handle,
                    ch_id,
                    None,
                    0,
                    seg,
                    0
                )

    def get_trigger_timing(self):
        """Retrieve per-capture trigger intervals and store them."""
        n_caps = self.seg_caps or self.dev_conf.capture_run.caps_in_run
        trig_info = (Trigger_Info * n_caps)()
        ps.ps5000aGetTriggerInfoBulk(
            self.dev_conf.mode.handle,
            ctypes.byref(trig_info),
            0,
            n_caps - 1,
        )

        samp_time = self.dev_conf.mode.samp_time
        last_ctr  = 0
        deltas    = []

        for i in trig_info:
            delta_ctr = i.timeStampCounter - last_ctr
            deltas.append(delta_ctr * samp_time)
            last_ctr = i.timeStampCounter

        self.buffer_manager.trigger_times.extend(deltas)
        self.buffer_manager.add_trigger_intervals(deltas)

    def ping_scope(self):
        """Responsible for checking the connection to the picoscope is still live."""
        if (ps.ps5000aPingUnit(self.dev_conf.mode.handle)) == 0:
            return True
        else:
            return False

    def get_cap_count(self):
        """Query PicoScope to check how many traces have been captured."""
        caps = ctypes.c_uint32(0)
        ps.ps5000aGetNoOfCaptures(self.dev_conf.mode.handle, ctypes.byref(caps))
        self.seg_caps = caps.value
        self.dev_conf.capture_run.live_cap_comp = (
            self.dev_conf.capture_run.caps_comp + caps.value
        )

    def calc_max_caps(self):
        """Calculate maximum amount of captures.

        Counteract the memory issues discovered. Uses a maximum amount of samples to
        recommend a maximum amount of captures for the user to collect.
        """
        active_chans = len(self.buffer_manager.active_channels)
        if active_chans == 0:
            active_chans = 1

        total_caps = (self.util.max_samples(self.dev_conf.mode.resolution) / active_chans)
        total_samples = self.dev_conf.capture.pre_trig_samples + (
            self.dev_conf.capture.post_trig_samples)
        self.rec_caps = int(round((total_caps / total_samples), 0))

    def stop_scope(self):
        """Tell scope to stop activity and close connection."""
        self.pico_status.stop = ps.ps5000aStop(self.dev_conf.mode.handle)
        self.pico_status.close = ps.ps5000aCloseUnit(self.dev_conf.mode.handle)
        if self.pico_status.stop == 0:
            self.pico_status.open_unit = -1
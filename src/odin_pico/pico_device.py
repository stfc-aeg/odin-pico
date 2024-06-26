"""Manage the PicoScope in preparing for, and extracting the data."""

import ctypes
import time

from picosdk.functions import mV2adc
from picosdk.ps5000a import ps5000a as ps

from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus
from odin_pico.pico_util import PicoUtil
from odin_pico.PS5000A_Trigger_Info import Trigger_Info
from odin_pico.file_writer import FileWriter


class PicoDevice:
    """Class that communicates with the scope to collect data."""

    def __init__(
        self,
        max_samples,
        dev_conf=DeviceConfig(),
        pico_status=DeviceStatus(),
        buffer_manager=BufferManager(),
        file_writer=FileWriter()
    ):
        """Initialise the PicoDevice class."""
        self.util = PicoUtil()
        self.dev_conf = dev_conf
        self.pico_status = pico_status
        self.buffer_manager = buffer_manager
        self.file_writer = file_writer
        self.cap_time = 30
        self.seg_caps = 0
        self.prev_seg_caps = 0
        self.channels = [
            self.dev_conf.channel_a,
            self.dev_conf.channel_b,
            self.dev_conf.channel_c,
            self.dev_conf.channel_d,
        ]
        self.max_samples = max_samples
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

    def assign_pico_memory(self):
        """Give PicoScope memory locations for data to be extracted.

        Map the local buffers in the buffer_manager to the picoscope for
        each individual trace to be captured on each channel by the picoscope.
        """
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
            for i in range(self.dev_conf.capture_run.caps_in_run):
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

            ps.ps5000aSetChannel(
                self.dev_conf.mode.handle,
                chan.channel_id,
                int(chan.active),
                chan.coupling,
                chan.range,
                chan.offset,
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

    def run_tb_setup(self):
        """Prepare the scope for a time-based capture."""
        # Open the scope if not already open
        if self.pico_status.open_unit != 0:
            self.open_unit()

        if self.pico_status.open_unit == 0:
            self.set_channels()
            self.set_trigger()
            return True

    def run_block(self):
        """Complete a PicoScope capture run using the rapid block mode.

        Responsible for telling the picoscope how much data to collect and
        when to collect it, retrives that data into local buffers once
        data collection is finished.
        """
        self.prev_seg_caps = 0
        self.seg_caps = 0
        # Keep track of time in case it takes too long
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

        # Send command to the scope to begin the rapid block mode
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
                self.pico_status.flags.system_state = "Waiting for Trigger"
                t = time.time()
                self.get_cap_count()

            if (time.time() - start_time) > 10:
                self.get_cap_count()
                if self.seg_caps == 0:
                    self.pico_status.flags.abort_cap = True

            # Stop scope if user chooses to abort capture
            if self.pico_status.flags.abort_cap:
                ps.ps5000aStop(self.dev_conf.mode.handle)
                collect = False

            time.sleep(0.05)
            self.prev_seg_caps = self.seg_caps

        self.pico_status.flags.system_state = current_system_state
        self.get_cap_count()
        if not self.file_writer.file_error and not self.pico_status.flags.user_capture:
            self.pico_status.flags.system_state = "Collecting LV Data"

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

    def get_trigger_timing(self):
        """Retrieve the trigger timing from the scope."""
        trigger_info = (Trigger_Info * self.dev_conf.capture_run.caps_in_run)()
        ps.ps5000aGetTriggerInfoBulk(
            self.dev_conf.mode.handle,
            ctypes.byref(trigger_info),
            0,
            (self.dev_conf.capture_run.caps_in_run - 1),
        )
        last_samples = 0

        for i in trigger_info:
            sample_interval = i.timeStampCounter - last_samples
            time_interval = sample_interval * self.dev_conf.mode.samp_time
            last_samples = i.timeStampCounter
            self.buffer_manager.trigger_times.append(time_interval)

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

        total_caps = (self.max_samples / active_chans)
        total_samples = self.dev_conf.capture.pre_trig_samples + (
            self.dev_conf.capture.post_trig_samples)
        self.rec_caps = int(round((total_caps / total_samples), 0))

    def calc_max_time(self):
        """Calculate maximum amount of time for time-based capture.

        Similar to calc_max_caps, this is to counteract the memory issues.
        """
        active_chans = len(self.buffer_manager.active_channels)
        if active_chans == 0:
            active_chans = 1

        times = sum(self.buffer_manager.trigger_times)

        self.rec_time = float(round((times * self.rec_caps), 2))

    def stop_scope(self):
        """Tell scope to stop activity and close connection."""
        self.pico_status.stop = ps.ps5000aStop(self.dev_conf.mode.handle)
        self.pico_status.close = ps.ps5000aCloseUnit(self.dev_conf.mode.handle)
        if self.pico_status.stop == 0:
            self.pico_status.open_unit = -1

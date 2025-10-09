from __future__ import annotations
import logging
import math
import re
import time
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from odin_pico.pico_controller import PicoController

from odin_pico.Utilities.pico_util import PicoUtil

class ControllerUtil:
    def __init__(self, controller:PicoController):
        self.controller = controller
        self.util = PicoUtil()

    def verify_gpib_avail(self):
        """verify that GPIB drivers are installed, USB Device is connected,
        Adapter is loaded and valid K2510 device is connected"""
        try:
            return (
                bool(self.controller.gpib) and
                bool(self.controller.gpib.gpibmanager.driver_available) and
                bool(self.controller.gpib.gpibmanager.device_available) and
                bool(self.controller.gpib_config.tec_devices)
            )
        except AttributeError:
            return False
    
    def verify_settings(self):
        """Verify all picoscope settings, sets status of individual groups of settings."""
        # Create list of Boolean values as to whether a channel is active or not
        channels = [
            getattr(self.controller.dev_conf, f"channel_{name}")
            for name in self.controller.dev_conf.channel_names
        ]
        active_flags = [ch.active for ch in channels]

        self.controller.pico_status.pico_setup_verify = self.verify_mode_settings(
            active_flags, self.controller.dev_conf.mode
        )
        for chan in channels:
            chan.verified = self.verify_channel_settings(chan.offset)
        self.controller.pico_status.channel_setup_verify = self.set_channel_verify_flag(
            channels
        )
        self.controller.pico_status.channel_trigger_verify = self.verify_trigger(
            channels, self.controller.dev_conf.trigger
        )
        self.controller.pico_status.capture_settings_verify = self.verify_capture(
            self.controller.dev_conf.capture
        )
        self.controller.pico_status.flags.verify_all = self.set_verify_flag()

    def verify_mode_settings(self, chan_active, mode):
        """Check if chosen PicoScope settings are logically correct."""
        channel_count = 0

        for chan in chan_active:
            if chan:
                channel_count += 1

        if mode.resolution == 1:
            if mode.timebase < 1:
                return -1
            elif mode.timebase == 1 and channel_count > 0 and channel_count < 2:
                return 0
            elif mode.timebase == 2 and channel_count > 0 and channel_count < 3:
                return 0
            elif mode.timebase >= 3 and channel_count > 0 and channel_count <= 4:
                return 0
            else:
                return -1

        if mode.resolution == 0:
            if mode.timebase < 0:
                return -1
            elif mode.timebase == 0 and channel_count > 0 and channel_count < 2:
                return 0
            elif mode.timebase == 1 and channel_count > 0 and channel_count < 3:
                return 0
            elif mode.timebase >= 2 and channel_count > 0 and channel_count <= 4:
                return 0
            else:
                return -1

        if channel_count == 0:
            return -1
        
    def verify_channel_settings(self, offset):
        """Check if chosen channel settings are logically correct."""
        if (offset >= -100) and (offset <= 100):
            return True
        else:
            return False
        
    def verify_trigger(self, channels, trigger):
        """Check if chosen trigger settings are logically correct."""
        source_chan = channels[trigger.source]
        if not (source_chan.active):
            return -1
        if trigger.threshold > self.util.get_range_value_mv(source_chan.range):
            return -1
        if not (trigger.delay >= 0 and trigger.delay <= 4294967295): #(replace with 2^) ctypes 32 in check
            return -1
        if not (trigger.auto_trigger_ms >= 0 and trigger.auto_trigger_ms <= 32767): #replace
            return -1
        return 0
    
    def verify_capture(self, capture):
        """Check if chosen capture settings are logically correct."""
        total_samples = capture.pre_trig_samples + capture.post_trig_samples
        if total_samples < 1:
            return -1
        if capture.n_captures < 1:
            return -1
        return 0
        
    def set_channel_verify_flag(self, channels):
        """Clarify if channel settings are verified, even when channel is active."""
        error_count = 0
        for chan in channels:
            if (chan.active) and (not chan.verified):
                error_count += 1
        if error_count == 0:
            return 0
        else:
            return -1

    def set_verify_flag(self):
        """Check if PicoScope settings are verified."""
        status_list = [
            self.controller.pico_status.pico_setup_verify,
            self.controller.pico_status.channel_setup_verify,
            self.controller.pico_status.channel_trigger_verify,
            self.controller.pico_status.capture_settings_verify,
        ]

        # Check if there are any issues with the statuses above
        for status in status_list:
            if status != 0:
                return False
        return True
    
    def set_capture_run_limits(self):
        """Set the value for maximum amount of captures that can fit into the picoscope memory."""
        # Calculate the amount of samples in a capture
        capture_samples = (
            self.controller.dev_conf.capture.pre_trig_samples
            + self.controller.dev_conf.capture.post_trig_samples
        )
        # Calculate the maximum amount of captures depending on settings
        #logging.debug(f"caps_max: {self.controller.dev_conf.capture_run.caps_max}")
        self.controller.dev_conf.capture_run.caps_max = math.floor(
            self.controller.util.max_samples(self.controller.dev_conf.mode.resolution) / capture_samples
        )

        if len(self.controller.buffer_manager.active_channels) > 1:
            self.controller.dev_conf.capture_run.caps_max /= len(self.controller.buffer_manager.active_channels)

        self.controller.dev_conf.capture_run.caps_remaining = self.controller.dev_conf.capture.n_captures

    def set_capture_run_length(self):
        """Sets the captures to be completed in each "run" based on the maximum allowed captures, and the amount of captures left to be collected"""

        if self.controller.dev_conf.capture_run.caps_remaining <= self.controller.dev_conf.capture_run.caps_max:
            self.controller.dev_conf.capture_run.caps_in_run = self.controller.dev_conf.capture_run.caps_remaining
        else:
            self.controller.dev_conf.capture_run.caps_in_run = self.controller.dev_conf.capture_run.caps_max

    def calc_samp_time(self):
        """Calculate the sample interval based on the resolution and timebase."""
        if self.controller.dev_conf.mode.resolution == 0:
            if (self.controller.dev_conf.mode.timebase) >= 0 and (
                self.controller.dev_conf.mode.timebase <= 2
            ):
                self.controller.dev_conf.mode.samp_time = math.pow(
                    2, self.controller.dev_conf.mode.timebase
                ) / (1000000000)
            else:
                self.controller.dev_conf.mode.samp_time = (self.controller.dev_conf.mode.timebase - 2) / (
                    125000000
                )
        elif self.controller.dev_conf.mode.resolution == 1:
            if (self.controller.dev_conf.mode.timebase) >= 1 and (
                self.controller.dev_conf.mode.timebase <= 3
            ):
                self.controller.dev_conf.mode.samp_time = math.pow(
                    2, self.controller.dev_conf.mode.timebase - 1
                ) / (500000000)
            else:
                self.controller.dev_conf.mode.samp_time = (self.controller.dev_conf.mode.timebase - 3) / (
                    62500000
                )

    def check_res(self):
        """Detect if the device resolution has been changed, if so, apply to picoscope."""
        if self.controller.pico_status.flags.res_changed:
            if self.controller.pico_status.open_unit == 0:
                self.controller.pico.stop_scope()
            self.controller.pico_status.flags.res_changed = False
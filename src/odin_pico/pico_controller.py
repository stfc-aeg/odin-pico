"""File to control the PicoScope processing."""

import logging
import math
import time
from concurrent import futures
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.concurrent import run_on_executor

from odin_pico.analysis import PicoAnalysis
from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus
from odin_pico.file_writer import FileWriter
from odin_pico.pico_device import PicoDevice
from odin_pico.pico_util import PicoUtil


class PicoController:
    """Class which holds parameter trees and manages the PicoScope capture process."""

    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, lock, loop, path, max_caps):
        """Initialise the PicoController Class."""
        # Threading lock and control variables
        self.lock = lock
        self.update_loop_active = loop

        # Initialise variables for data collection
        self.enable = False
        self.caps_collected = 0
        self.current_time = 0
        self.current_capture = 0

        # Objects for handling configuration, data storage and representing the PicoScope 5444D
        self.dev_conf = DeviceConfig()
        self.dev_conf.file.file_path = path
        self.channels = [
            self.dev_conf.channel_a,
            self.dev_conf.channel_b,
            self.dev_conf.channel_c,
            self.dev_conf.channel_d,
        ]

        # Initialise objects
        self.util = PicoUtil()
        self.pico_status = DeviceStatus()
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf, self.buffer_manager, self.pico_status)
        self.analysis = PicoAnalysis(
            self.dev_conf, self.buffer_manager, self.pico_status
        )
        self.pico = PicoDevice(max_caps, self.dev_conf, self.pico_status,
                               self.buffer_manager, self.file_writer)

        # ParameterTrees to represent different parts of the system
        adapter_status = ParameterTree(
            {
                "settings_verified": (lambda: self.pico_status.flags.verify_all, None),
                "open_unit": (lambda: self.pico_status.open_unit, None),
                "pico_setup_verify": (lambda: self.pico_status.pico_setup_verify, None),
                "channel_setup_verify": (
                    lambda: self.pico_status.channel_setup_verify,
                    None,
                ),
                "channel_trigger_verify": (
                    lambda: self.pico_status.channel_trigger_verify,
                    None,
                ),
                "capture_settings_verify": (
                    lambda: self.pico_status.capture_settings_verify,
                    None,
                ),
            }
        )

        self.chan_params = {}
        for name in self.dev_conf.channel_names:
            self.chan_params[name] = ParameterTree(
                {
                    "channel_id": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "channel_id",
                        ),
                        None,
                    ),
                    "active": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "active",
                        ),
                        partial(
                            self.set_dc_chan_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "active",
                        ),
                    ),
                    "verified": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "verified",
                        ),
                        None,
                    ),
                    "live_view": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "live_view",
                        ),
                        partial(
                            self.set_dc_chan_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "live_view",
                        ),
                    ),
                    "coupling": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "coupling",
                        ),
                        partial(
                            self.set_dc_chan_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "coupling",
                        ),
                    ),
                    "range": (
                        partial(
                            self.get_dc_value, self.dev_conf, f"channel_{name}", "range"
                        ),
                        partial(
                            self.set_dc_chan_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "range",
                        ),
                    ),
                    "offset": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "offset",
                        ),
                        partial(
                            self.set_dc_chan_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "offset",
                        ),
                    ),
                    "pha_active": (
                        partial(
                            self.get_dc_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "pha_active",
                        ),
                        partial(
                            self.set_dc_chan_value,
                            self.dev_conf,
                            f"channel_{name}",
                            "pha_active",
                        ),
                    ),
                }
            )

        pico_trigger = ParameterTree(
            {
                "active": (
                    lambda: self.dev_conf.trigger.active,
                    partial(self.set_dc_value, self.dev_conf.trigger, "active"),
                ),
                "auto_trigger": (
                    lambda: self.dev_conf.trigger.auto_trigger_ms,
                    partial(
                        self.set_dc_value, self.dev_conf.trigger, "auto_trigger_ms"
                    ),
                ),
                "direction": (
                    lambda: self.dev_conf.trigger.direction,
                    partial(self.set_dc_value, self.dev_conf.trigger, "direction"),
                ),
                "delay": (
                    lambda: self.dev_conf.trigger.delay,
                    partial(self.set_dc_value, self.dev_conf.trigger, "delay"),
                ),
                "source": (
                    lambda: self.dev_conf.trigger.source,
                    partial(self.set_dc_value, self.dev_conf.trigger, "source"),
                ),
                "threshold": (
                    lambda: self.dev_conf.trigger.threshold,
                    partial(self.set_dc_value, self.dev_conf.trigger, "threshold"),
                ),
            }
        )

        pico_capture = ParameterTree(
            {
                "pre_trig_samples": (
                    lambda: self.dev_conf.capture.pre_trig_samples,
                    partial(
                        self.set_dc_value, self.dev_conf.capture, "pre_trig_samples"
                    ),
                ),
                "post_trig_samples": (
                    lambda: self.dev_conf.capture.post_trig_samples,
                    partial(
                        self.set_dc_value, self.dev_conf.capture, "post_trig_samples"
                    ),
                ),
                "n_captures": (
                    lambda: self.dev_conf.capture.n_captures,
                    partial(self.set_dc_value, self.dev_conf.capture, "n_captures"),
                ),
                "capture_time": (
                    lambda: self.dev_conf.capture.capture_time,
                    partial(self.set_dc_value, self.dev_conf.capture, "capture_time"),
                ),
                "capture_mode": (
                    lambda: self.dev_conf.capture.capture_type,
                    partial(self.set_dc_value, self.dev_conf.capture, "capture_type"),
                ),
                "capture_delay": (
                    lambda: self.dev_conf.capture.capture_delay,
                    partial(self.set_dc_value, self.dev_conf.capture, "capture_delay"),
                ),
                "repeat_amount": (
                    lambda: self.dev_conf.capture.repeat_amount,
                    partial(self.set_dc_value, self.dev_conf.capture, "repeat_amount"),
                ),
                "capture_repeat": (
                    lambda: self.dev_conf.capture.capture_repeat,
                    partial(self.set_dc_value, self.dev_conf.capture, "capture_repeat"),
                ),
                "max_captures": (lambda: self.pico.rec_caps, None),
                "max_time": (lambda: self.pico.rec_time, None)
            }
        )

        pico_mode = ParameterTree(
            {
                "resolution": (
                    lambda: self.dev_conf.mode.resolution,
                    partial(self.set_dc_value, self.dev_conf.mode, "resolution"),
                ),
                "timebase": (
                    lambda: self.dev_conf.mode.timebase,
                    partial(self.set_dc_value, self.dev_conf.mode, "timebase"),
                ),
                "samp_time": (lambda: self.dev_conf.mode.samp_time, None),
            }
        )

        pico_file = ParameterTree(
            {
                "folder_name": (
                    lambda: self.dev_conf.file.folder_name,
                    partial(self.set_dc_value, self.dev_conf.file, "folder_name"),
                ),
                "file_name": (
                    lambda: self.dev_conf.file.file_name,
                    partial(self.set_dc_value, self.dev_conf.file, "file_name"),
                ),
                "file_path": (lambda: self.dev_conf.file.file_path, None),
                "curr_file_name": (lambda: self.dev_conf.file.curr_file_name, None),
                "last_write_success": (
                    lambda: self.dev_conf.file.last_write_success,
                    None,
                ),
            }
        )

        pico_pha = ParameterTree(
            {
                "num_bins": (
                    lambda: self.dev_conf.pha.num_bins,
                    partial(self.set_dc_value, self.dev_conf.pha, "num_bins"),
                ),
                "lower_range": (
                    lambda: self.dev_conf.pha.lower_range,
                    partial(self.set_dc_value, self.dev_conf.pha, "lower_range"),
                ),
                "upper_range": (
                    lambda: self.dev_conf.pha.upper_range,
                    partial(self.set_dc_value, self.dev_conf.pha, "upper_range"),
                ),
            }
        )

        pico_settings = ParameterTree(
            {
                "mode": pico_mode,
                "channels": {
                    name: channel for (name, channel) in self.chan_params.items()
                },
                "trigger": pico_trigger,
                "capture": pico_capture,
                "file": pico_file,
                "pha": pico_pha,
            }
        )

        live_view = ParameterTree(
            {
                "lv_active_channels": (
                    lambda: self.buffer_manager.lv_channels_active,
                    None,
                ),
                "pha_counts": (lambda: self.buffer_manager.pha_counts, None),
                "capture_count": (
                    lambda: self.dev_conf.capture_run.live_cap_comp,
                    None,
                ),
                "captures_requested": (lambda: self.dev_conf.capture.n_captures, None),
                "lv_data": (lambda: self.buffer_manager.lv_channel_arrays, None),
                "pha_bin_edges": (lambda: self.buffer_manager.bin_edges, None),
                "lv_range": (
                    lambda: self.buffer_manager.lv_range,
                    partial(self.set_dc_value, self.buffer_manager, "lv_range"),
                ),
                "pha_active_channels": (
                    lambda: self.buffer_manager.pha_active_channels,
                    None,
                ),
                "current_tbdc_time": (lambda: self.current_time, None),
                "current_capture": (lambda: self.current_capture, None),
            }
        )

        pico_commands = ParameterTree(
            {
                "run_user_capture": (
                    lambda: self.pico_status.flags.user_capture,
                    partial(self.set_dc_value, self.pico_status.flags, "user_capture"),
                ),
                "clear_pha": (
                    lambda: self.analysis.clear_pha,
                    partial(self.set_dc_value, self.analysis, "clear_pha"),
                ),
            }
        )

        pico_flags = ParameterTree(
            {
                "abort_cap": (
                    lambda: self.pico_status.flags.abort_cap,
                    partial(self.set_dc_value, self.pico_status.flags, "abort_cap"),
                ),
                "system_state": (lambda: self.pico_status.flags.system_state, None),
            }
        )

        self.pico_param_tree = ParameterTree(
            {
                "status": adapter_status,
                "commands": pico_commands,
                "settings": pico_settings,
                "flags": pico_flags,
                "live_view": live_view,
            }
        )

        self.param_tree = ParameterTree({"device": self.pico_param_tree})

        # Initalise the "update_loop" if control variable passed to the Pico_Controller is True
        if self.update_loop_active:
            self.update_loop()

        # Set initial state of the verification system
        self.verify_settings()

    def get_dc_value(self, obj, chan_name, attr_name):
        """Retrive values for the live-view settings."""
        try:
            channel_dc = getattr(obj, chan_name)
            return getattr(channel_dc, attr_name, None)
        except AttributeError:
            return None

    def set_dc_value(self, obj, attr_name, value):
        """Change values for the live-view settings."""
        # Check if PHA needs to be reset
        if (
            (attr_name == "num_bins")
            or (attr_name == "lower_range")
            or (attr_name == "upper_range")
        ):
            self.analysis.clear_pha = True

        # Ensure a negative value has not been entered
        if attr_name == "pre_trig_samples" or attr_name == "post_trig_samples" or (
            attr_name == "auto-trigger_ms") or attr_name == "delay" or (
                attr_name == "capture_delay"):
            if value < 0:
                value = value * (-1)

        # Check setting validity
        # Check upper range is not lower than lower range, and vice versa
        if attr_name == "upper_range":
            if value < self.dev_conf.pha.lower_range:
                value = self.dev_conf.pha.lower_range + 1

        if attr_name == "lower_range":
            if value < 0:
                value = value * (-1)

            if value > self.dev_conf.pha.upper_range:
                value = self.dev_conf.pha.upper_range - 1

        if attr_name == "num_bins" or attr_name == "n_captures" or attr_name == "repeat_amount":
            if value < 1:
                value = 1

        if attr_name == "capture_time":
            if value <= 0:
                value = value * (-1)

        setattr(obj, attr_name, value)

    def set_dc_chan_value(self, obj, chan_name, attr_name, value):
        """Change values for the individual channel settings."""
        # Ensure the user does not input a negative offset
        if attr_name == "offset":
            if value < 0:
                value = value * (-1)

        # Check setting validity
        # Check if channel selected for LV is actually active
        if attr_name == "live_view":
            try:
                channel_dc = getattr(obj, chan_name)
                if getattr(channel_dc, "active", None):
                    setattr(channel_dc, attr_name, value)
            except AttributeError:
                pass

        # When channels turn off, ensure they are not LV/PHA active
        elif (attr_name == "active") and (not value):
            try:
                channel_dc = getattr(obj, chan_name)
                setattr(channel_dc, "live_view", value)
                setattr(channel_dc, 'pha_active', value)
                setattr(channel_dc, attr_name, value)
            except AttributeError:
                pass
        else:
            try:
                channel_dc = getattr(obj, chan_name)
                setattr(channel_dc, attr_name, value)
            except AttributeError:
                pass

    def verify_settings(self):
        """Verify all picoscope settings, sets status of individual groups of settings."""
        # Create list of Boolean values as to whether a channel is active or not
        active = [
            self.dev_conf.channel_a.active,
            self.dev_conf.channel_b.active,
            self.dev_conf.channel_c.active,
            self.dev_conf.channel_d.active,
        ]

        # Use functions to verify all of the chosen settings
        self.pico_status.pico_setup_verify = self.util.verify_mode_settings(
            active, self.dev_conf.mode
        )
        for chan in self.channels:
            chan.verified = self.util.verify_channel_settings(chan.offset)
        self.pico_status.channel_setup_verify = self.util.set_channel_verify_flag(
            self.channels
        )
        self.pico_status.channel_trigger_verify = self.util.verify_trigger(
            self.channels, self.dev_conf.trigger
        )
        self.pico_status.capture_settings_verify = self.util.verify_capture(
            self.dev_conf.capture
        )
        self.pico_status.flags.verify_all = self.set_verify_flag()

    def set_verify_flag(self):
        """Check if PicoScope settings are verified."""
        status_list = [
            self.pico_status.pico_setup_verify,
            self.pico_status.channel_setup_verify,
            self.pico_status.channel_trigger_verify,
            self.pico_status.capture_settings_verify,
        ]

        # Check if there are any issues with the statuses above
        for status in status_list:
            if status != 0:
                return False
        return True

    def set_capture_run_limits(self, captures):
        """Set the value for maximum amount of captures that can fit into the picoscope memory."""
        # Calculate the amount of samples in a capture
        capture_samples = (
            self.dev_conf.capture.pre_trig_samples
            + self.dev_conf.capture.post_trig_samples
        )

        # Calculate the maximum amount of captures depending on settings
        self.dev_conf.capture_run.caps_max = math.floor(
            self.util.max_samples(self.dev_conf.mode.resolution) / capture_samples
        )
        self.dev_conf.capture_run.caps_remaining = captures

    def set_capture_run_length(self):
        """Set the captures to be completed in each "run" based on the maximum allowed captures."""
        # Avoid dividing by zero, set max caps depending on active channels
        if len(self.buffer_manager.active_channels) > 0:
            max_caps = math.trunc(
                (self.dev_conf.capture_run.caps_max)
                / (len(self.buffer_manager.active_channels))
            )
        else:
            max_caps = self.dev_conf.capture_run.caps_max

        # Calculate captures left to collect
        if self.dev_conf.capture_run.caps_remaining <= max_caps:
            self.dev_conf.capture_run.caps_in_run = (
                self.dev_conf.capture_run.caps_remaining
            )
        else:
            self.dev_conf.capture_run.caps_in_run = max_caps

    def calc_samp_time(self):
        """Calculate the sample interval based on the resolution and timebase."""
        if self.dev_conf.mode.resolution == 0:
            if (self.dev_conf.mode.timebase) >= 0 and (
                self.dev_conf.mode.timebase <= 2
            ):
                self.dev_conf.mode.samp_time = math.pow(
                    2, self.dev_conf.mode.timebase
                ) / (1000000000)
            else:
                self.dev_conf.mode.samp_time = (self.dev_conf.mode.timebase - 2) / (
                    125000000
                )
        elif self.dev_conf.mode.resolution == 1:
            if (self.dev_conf.mode.timebase) >= 1 and (
                self.dev_conf.mode.timebase <= 3
            ):
                self.dev_conf.mode.samp_time = math.pow(
                    2, self.dev_conf.mode.timebase - 1
                ) / (500000000)
            else:
                self.dev_conf.mode.samp_time = (self.dev_conf.mode.timebase - 3) / (
                    62500000
                )

    def run_capture(self):
        """Tell the picoscope to collect and return data."""
        self.calc_samp_time()

        if self.pico_status.flags.verify_all:
            self.check_res()

            # Check if user has requested a capture
            if self.pico_status.flags.user_capture:
                if self.file_writer.check_file_name():

                    self.file_writer.file_error = False

                    # Check if user has requested the capture to be repeated
                    if self.dev_conf.capture.capture_repeat:
                        cap_loop = self.dev_conf.capture.repeat_amount
                        delay = self.dev_conf.capture.capture_delay
                    else:
                        cap_loop = 1
                        delay = 0

                    for capture_run in range(cap_loop):
                        self.buffer_manager.pha_counts = [[]] * 4

                        self.buffer_manager.pha_counts = [[]] * 4
                        self.current_capture = capture_run
                        self.current_time = 0

                        # Complete a capture run, based on capture number
                        if not self.dev_conf.capture.capture_type:
                            if not self.pico_status.flags.abort_cap:
                                self.pico_status.flags.system_state = (
                                    "Collecting Requested Captures, Capture: " + str(
                                        capture_run + 1)
                                )
                                self.user_capture(True)
                        else:
                            # Complete a capture test, to determine capture frequency
                            if capture_run == 0:
                                self.pico_status.flags.system_state = ("Testing Capture Rate")
                                # self.caps_per_cycle()
                                self.buffer_manager.pha_counts = [[]] * 4

                            # Complete a capture run, for a pre-determined amount of time
                            if not self.pico_status.flags.abort_cap:
                                self.pico_status.flags.system_state = (
                                    "Completing Time-Based Capture Collection, Capture: "
                                    + str(capture_run + 1)
                                )
                                self.tb_capture()

                        # Delay between capture runs, if requested by user
                        if capture_run != (cap_loop - 1):
                            self.pico_status.flags.system_state = ("Delay Between Captures")
                            start_time = time.time()
                            while (time.time() - start_time) < delay:
                                if self.pico_status.flags.abort_cap:
                                    delay = 0

                        # Change system state, depends on if capture was repeated
                        if (capture_run + 1) == cap_loop:
                            self.current_time = 0

                    self.current_capture = 0
                    self.file_writer.capture_number = 1
                    self.pico_status.flags.user_capture = False
                    self.pico_status.flags.abort_cap = False

                else:
                    self.file_writer.file_error = True
                    self.pico_status.flags.system_state = (
                        "File Name Empty or Already Exists. Fix and Re-Capture")
                    self.pico_status.flags.user_capture = False

            # If user hasn't requested a capture, complete a LV capture run
            else:
                if not self.file_writer.file_error:
                    self.pico_status.flags.system_state = "Collecting LV Data"
                self.pico.calc_max_caps()
                self.user_capture(False)
                self.pico_status.flags.abort_cap = False

        if (self.pico_status.open_unit == 0) and (
            self.pico_status.flags.verify_all is False
        ):
            self.pico_status.flags.system_state = "Connected to PicoScope, Idle"

    def check_res(self):
        """Detect if the device resolution has been changed, if so apply to picoscope."""
        if self.pico_status.flags.res_changed:
            if self.pico_status.open_unit == 0:
                self.pico.stop_scope()
            self.pico_status.flags.res_changed = False

    def user_capture(self, save_file):
        """Run the appropriate steps for a set of captures."""
        # Identify whether the capture is a user capture or just for LV
        if save_file:
            captures = self.dev_conf.capture.n_captures
        else:
            captures = 10
        self.set_capture_run_limits(captures)

        if self.pico.run_setup():
            while self.dev_conf.capture_run.caps_comp < captures:
                if not self.pico_status.flags.abort_cap:
                    self.set_capture_run_length()
                    self.capture_run()
                    self.dev_conf.capture_run.caps_remaining -= (
                        self.dev_conf.capture_run.caps_in_run
                    )
                else:
                    self.dev_conf.capture_run.caps_comp = captures

            # Saves captures to a file, if requested
            if save_file:
                self.file_writer.write_hdf5()

        self.dev_conf.capture_run.reset()

    def capture_run(self):
        """Run the necessary steps for a capture."""
        # Run the scope, and update the captures completed
        self.pico.assign_pico_memory()
        self.pico.run_block()
        self.dev_conf.capture_run.caps_comp += self.pico.seg_caps * len(
            self.buffer_manager.active_channels
        )

        # Process the data, for the purposes of LV and PHA
        if not self.pico_status.flags.abort_cap:
            self.buffer_manager.save_lv_data()
            self.analysis.pha_one_peak()


    def tb_capture(self):
        """Run the necessary steps for a set of time-based captures."""
        self.buffer_manager.clear_arrays()
        self.buffer_manager.check_channels()
        total_time = self.dev_conf.capture.capture_time

        # Calculate the amount of captures to be collected per run
        self.dev_conf.capture_run.caps_in_run = math.trunc(
            self.dev_conf.capture.caps_in_cycle
            / (len(self.buffer_manager.active_channels))
        )

        self.buffer_manager.generate_tb_arrays()
        if self.pico.run_tb_setup():
            start_time = time.time()
            # Run the capture runs until the time is up
            while (time.time() - start_time) < total_time:
                if not self.pico_status.flags.abort_cap:
                    self.capture_run()
                else:
                    total_time = 0

                if (time.time() - start_time > total_time):
                    self.current_time = total_time
                else:
                    self.current_time = time.time() - start_time
            # Save data to file if requested
            self.file_writer.write_hdf5()

        self.caps_collected = self.dev_conf.capture_run.caps_comp
        self.dev_conf.capture_run.reset()

    ##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        """Execute thread, responsible for calling the run_capture function at timed intervals."""
        while self.update_loop_active:
            self.run_capture()
            time.sleep(0.2)

    def set_update_loop_state(self, state=bool):
        """Set the state of the update_loop in the executor thread."""
        self.update_loop_active = state

    def cleanup(self):
        """Responsible for ensuring the picoscope is closed cleanly when the adapter is shutdown."""
        self.set_update_loop_state(False)
        self.pico_status.flags.abort_cap = True
        self.pico.stop_scope()
        logging.debug("Stopping PicoScope services and closing device")

    def get(self, path):
        """Get the parameter tree."""
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree."""
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise PicoControllerError(e)
        self.verify_settings()

class PicoControllerError(Exception):
    pass

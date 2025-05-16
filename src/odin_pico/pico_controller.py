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

    def __init__(self, lock, loop, path, max_caps, simulate):
        """Initialise the PicoController Class."""
        # Threading lock and control variables
        self.lock = lock
        self.update_loop_active = loop
    
        self.gpib_avail = False
        self.gpib_control = False
        self.tec_devices = None
        self.selected_tec = None
        self.simulate = simulate

        self.temp_setpoint = None
        self.voltage_limit = None
        self.current_limit = None

        # Initialise variables for data collection
        self.enable = False
        self.caps_collected = 0
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
        self.buffer_manager = BufferManager(self.channels, self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf, self.buffer_manager, self.pico_status)
        self.analysis = PicoAnalysis(
            self.dev_conf, self.buffer_manager, self.pico_status
        )
        self.pico = PicoDevice(max_caps, self.dev_conf, self.pico_status,
                               self.buffer_manager, self.analysis, self.file_writer)
        
        self.param_tree = None
        self.gpib_tree = ParameterTree({
                    "gpib_avail": (lambda: self.gpib_avail, None),
                    "gpib_control": (lambda: self.gpib_control, lambda value: setattr(self, 'gpib_control', value)),
        })

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
                "max_time": (lambda: self.buffer_manager.estimate_max_time(), None)
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
                # "lv_range": (
                #     lambda: self.buffer_manager.lv_range,
                #     partial(self.set_dc_value, self.buffer_manager, "lv_range"),
                # ),
                "pha_active_channels": (
                    lambda: self.buffer_manager.pha_active_channels,
                    None,
                ),
                "current_tbdc_time": (lambda: self.pico.elapsed_time, None),
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

        self.device_tree = ParameterTree({"device": self.pico_param_tree})

        # Initalise the "update_loop" if control variable passed to the Pico_Controller is True
        if self.update_loop_active:
            self.update_loop()

        # Set initial state of the verification system
        self.verify_settings()

    def initialize_adapters(self, adapters):
        """Get access to all of the other adapters. If the GPIB adapter is running, 
        build a paramtree for a currently selected device."""
        try:
            self.gpib = adapters['gpib'] if adapters else None
        except:
            pass

        if self.gpib:
            devices = self.util.iac_get(self.gpib, "devices")
            self.tec_devices = [name for name, info in devices.items()
                if info.get("type") == "K2510"]

            self.gpib_avail = self.verify_gpib()

            if self.tec_devices:
                self.selected_tec = self.tec_devices[0]

                self.gpib_info = ParameterTree({
                    "tec_setpoint": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_setpoint"))), None),
                    "tec_volt_lim": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_volt_lim"))), None),
                    "tec_curr_lim": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_curr_lim"))), None),
                    "tec_current": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_current"))), None),
                    "tec_voltage": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_voltage"))), None),
                    "tec_power": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_power"))), None),
                    "tec_temp_meas": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/info/tec_temp_meas"))), None),
                })

                self.gpib_set = ParameterTree({
                    "temp": (lambda: (self.util.iac_get(self.gpib, 
                                ("devices/"+self.selected_tec+"/set/temp_set"))), 
                            lambda value: self.util.iac_set(self.gpib, 
                                ("devices/"+self.selected_tec+"/set/temp_set", float(value)))),
                    "c_lim": (lambda: (self.util.iac_get(self.gpib, 
                                ("devices/"+self.selected_tec+"/set/c_lim_set"))), 
                            lambda value: self.util.iac_set(self.gpib, 
                                ("devices/"+self.selected_tec+"/set/c_lim_set", float(value)))),
                    "v_lim": (lambda: (self.util.iac_get(self.gpib, 
                                ("devices/"+self.selected_tec+"/set/v_lim_set"))), 
                            lambda value: self.util.iac_set(self.gpib, 
                                ("devices/"+self.selected_tec+"/set/v_lim_set", float(value))))
                })

                self.gpib_temp_sweep = ParameterTree({
                    "active" : (lambda: self.dev_conf.temp_sweep.active,
                                lambda v: self.set_dc_value(self.dev_conf.temp_sweep, "active",  v)),
                    "t_start": (lambda: self.dev_conf.temp_sweep.t_start,
                                lambda v: self.set_dc_value(self.dev_conf.temp_sweep, "t_start", v)),
                    "t_end"  : (lambda: self.dev_conf.temp_sweep.t_end,
                                lambda v: self.set_dc_value(self.dev_conf.temp_sweep, "t_end",   v)),
                    "t_step" : (lambda: self.dev_conf.temp_sweep.t_step,
                                lambda v: self.set_dc_value(self.dev_conf.temp_sweep, "t_step",  v)),
                    "tol"    : (lambda: self.dev_conf.temp_sweep.tol,
                                lambda v: self.set_dc_value(self.dev_conf.temp_sweep, "tol",     v)),
                    "poll_s" : (lambda: self.dev_conf.temp_sweep.poll_s,
                                lambda v: self.set_dc_value(self.dev_conf.temp_sweep, "poll_s",  v)),
                })
                
                self.gpib_tree = ParameterTree(
                {
                    "gpib_avail": (lambda: self.gpib_avail, None),
                    "gpib_control": (lambda: self.gpib_control, lambda value: setattr(self, 'gpib_control', value)),
                    "available_tecs": (lambda: self.tec_devices, None),
                    "selected_tec": (lambda: self.selected_tec, lambda value: setattr(self, 'selected_tec', value)),
                    "device_control_state": (lambda: (self.util.iac_get(self.gpib, 
                                                ("devices/"+self.selected_tec+"/device_control_state"))), 
                                            lambda value: self.util.iac_set(self.gpib, 
                                                ("devices/"+self.selected_tec+"/"), {"device_control_state": value})),
                    "output_state": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/output_state"))), 
                                    lambda value: self.util.iac_set(self.gpib, 
                                        ("devices/"+self.selected_tec+"/"), {"output_state": value})),
                    "temp_over_state": (lambda: (self.util.iac_get(self.gpib, 
                                        ("devices/"+self.selected_tec+"/temp_over_state"))), 
                                    lambda value: self.util.iac_set(self.gpib, 
                                        ("devices/"+self.selected_tec+"/"), {"temp_over_state": value})),
                    "set": self.gpib_set,
                    "info": self.gpib_info,
                    "temp_sweep": self.gpib_temp_sweep
                })

        self.param_tree = ParameterTree({
            "device": self.pico_param_tree,
            "gpib": self.gpib_tree
        })

    def verify_gpib(self):
        """verify that GPIB drivers are installed, USB Device is connected,
        Adapter is loaded and valid K2510 device is connected"""
        try:
            return (
                bool(self.gpib) and
                bool(self.gpib.gpibmanager.driver_available) and
                bool(self.gpib.gpibmanager.device_available) and
                bool(self.tec_devices)
            )
        except AttributeError:
            return False

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

    def set_capture_run_limits(self):
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

        if len(self.buffer_manager.active_channels) > 1:
            self.dev_conf.capture_run.caps_max /= len(self.buffer_manager.active_channels)

        self.dev_conf.capture_run.caps_remaining = self.dev_conf.capture.n_captures

    def set_capture_run_length(self):
        """Sets the captures to be completed in each "run" based on the maximum allowed captures, and the amount of captures left to be collected"""

        if self.dev_conf.capture_run.caps_remaining <= self.dev_conf.capture_run.caps_max:
            self.dev_conf.capture_run.caps_in_run = self.dev_conf.capture_run.caps_remaining
        else:
            self.dev_conf.capture_run.caps_in_run = self.dev_conf.capture_run.caps_max

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
                        # reset abort flag if its been set by TB capture
                        self.pico_status.flags.abort_cap = False
                        ##why are pha_counts being appended twice? why here and not in buffer_manager?
                        self.buffer_manager.pha_counts = [[]] * 4
                        self.current_capture = capture_run

                        # Complete a capture run, based on capture number
                        if not self.dev_conf.capture.capture_type:
                            if not self.pico_status.flags.abort_cap:
                                self.pico_status.flags.system_state = (
                                    "Collecting Requested Captures, Capture: " + str(
                                        capture_run + 1)
                                )
                                # TEC-sweep
                                if (self.dev_conf.temp_sweep.active and
                                    self.gpib_control and
                                    self.gpib_avail):
                                    self.run_temperature_sweep()
                                else:
                                    self.user_capture(True)
                        else:
                            self.buffer_manager.pha_counts = [[]] * 4

                            # Complete a capture run, for a pre-determined amount of time
                            if not self.pico_status.flags.abort_cap:
                                self.pico_status.flags.system_state = (
                                    "Completing Time-Based Capture Collection, Capture: "
                                    + str(capture_run + 1)
                                )
                                # TEC-sweep
                                if (self.dev_conf.temp_sweep.active and
                                    self.gpib_control and
                                    self.gpib_avail):
                                    self.run_temperature_sweep()
                                else:
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
            captures = 2
            
        self.set_capture_run_limits()
        
        #set caps_remaining for liveview mode
        if not save_file:
            self.dev_conf.capture_run.caps_remaining = 2
            
        self.set_capture_run_length()
    
        # checks run_setup completes successfully, calls it with captures if save_file is not true
        if self.pico.run_setup() if save_file else self.pico.run_setup(captures):
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
        """
        """
        # validate this method of calculating max captures!
        self.set_capture_run_limits()
        self.dev_conf.capture_run.caps_in_run = int(self.dev_conf.capture_run.caps_max/2)
        self.pico.run_time_based_capture(
            self.dev_conf.capture.capture_time
            )
        self.file_writer.write_hdf5(write_accumulated=True)
        self.buffer_manager.clear_arrays()

    def wait_for_tec(self, target: float, tol: float):
        """Wait for tec for reach target temp within a set tolerance"""
        while not self.pico_status.flags.abort_cap:
            meas = self.util.iac_get(
                self.gpib,
                f"devices/{self.selected_tec}/info/tec_temp_meas")
            if meas is None:
                break
            if abs(meas - target) <= tol:
                return
            time.sleep(self.dev_conf.temp_sweep.poll_s)

    def _temp_range(self, start, end, step):
        """
        Return a list of temperatures in equal increments, direction is 
        inferred from start → end
        """
        if step == 0 or start == end:
            return [start]

        step      = abs(step) # ignore sign the user gave
        direction = 1 if end >= start else -1
        temps     = [start]
        current   = start

        while True:
            next_val = current + direction * step
            # Would the next step cross the end value?
            if (direction == 1 and next_val >= end) or \
            (direction == -1 and next_val <= end):
                break
            temps.append(next_val)
            current = next_val

        if temps[-1] != end:
            temps.append(end)

        logging.debug(f"returning temps: {temps}")
        return temps
    
    def _temp_suffix(self, T: float) -> str:
        """
        Return a filename-safe suffix like '_25-0c' or '_-5-0c'
        (1 decimal place, '.' → '-').
        """
        s = f"{T:.1f}".replace(".", "-")
        return f"_{s}c"
    
    def run_temperature_sweep(self):
        """
        Iterate over every temperature in the listeven in SIM mode
        and acquire data.  A guard flag prevents any single capture from
        setting `abort_cap` and killing the rest of the sweep.
        """
        sweep = self.dev_conf.temp_sweep
        if not sweep.active:
            return

        temps    = self._temp_range(sweep.t_start, sweep.t_end, sweep.t_step)
        logging.info(f"[TEC-sweep] Set-points: {temps}")

        base_fname = self.dev_conf.file.file_name.rstrip(".hdf5")

        # local flag so abort in one capture doesn’t cancel the sweep
        sweep_abort = False

        for idx, T in enumerate(temps):
            if sweep_abort:
                break

            # Set temperature on Tec
            if self.simulate:
                logging.info(f"[SIM] TEC set-point → {T:.2f} °C")
            else:
                self.util.iac_set(
                    self.gpib,
                    f"devices/{self.selected_tec}/set/temp_set",
                    float(T)
                )
            self.buffer_manager.temp_set_last = T

            # ── 2) wait / mock wait until stable ────────────────────────────
            self.pico_status.flags.system_state = (
                f"{'Simulating' if self.simulate else 'Waiting for'} TEC {T:.2f} °C")

            if self.simulate:
                time.sleep(sweep.poll_s)
                self.buffer_manager.temp_meas_last = T
            else:
                self.wait_for_tec(T, sweep.tol)
                self.buffer_manager.temp_meas_last = self.util.iac_get(
                    self.gpib,
                    f"devices/{self.selected_tec}/info/tec_temp_meas")

            # ── 3) make a unique file name for this temperature ─────────────
            self.dev_conf.file.file_name = \
                base_fname + self._temp_suffix(T)      # no “.hdf5” here
            self.file_writer.capture_number = 1        # reset suffix counter

            # ── 4) run the acquisition in current mode ──────────────────────
            self.pico_status.flags.system_state = \
                f"Capturing @ {T:.2f} °C  ({idx+1}/{len(temps)})"

            # reset abort flag before each capture; if *this* capture sets it,
            # finish the file and then abandon the remaining temps
            self.pico_status.flags.abort_cap = False

            try:
                if self.dev_conf.capture.capture_type:     # time-based
                    self.tb_capture()
                else:                                      # fixed-count
                    self.user_capture(True)
            except Exception as e:
                logging.error(f"Capture failed at {T}°C: {e}")
                sweep_abort = True

        # restore original file name for future manual runs
        self.dev_conf.file.file_name = base_fname + ".hdf5"
        self.pico_status.flags.system_state = (
            "TEC Sweep Aborted" if sweep_abort else "TEC Sweep Complete")

        
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

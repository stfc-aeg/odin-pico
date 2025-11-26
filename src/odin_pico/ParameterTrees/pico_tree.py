from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odin_pico.pico_controller import PicoController

from functools import partial
from odin.adapters.parameter_tree import ParameterTree
from odin_pico.Utilities.param_tree import get_dc_value, set_dc_value, set_dc_chan_value

class PicoTreeBuilder:
    """Class to build PicoScope-related parameter trees."""
    
    def __init__(self, controller:PicoController):
        """Initialize with controller reference and extract needed dependencies."""
        self.controller = controller
        self.dev_conf = controller.dev_conf
        self.pico_status = controller.pico_status
        self.analysis = controller.analysis
        self.buffer_manager = controller.buffer_manager
        self.pico = controller.pico
        self.gpib_config = controller.gpib_config  # Keep this for live_view references
        self.gpio_config = controller.gpio_config
        
    def create_adapter_status_tree(self):
        """Create the adapter status parameter tree."""
        return ParameterTree({
            "settings_verified": (lambda: self.pico_status.flags.verify_all, None),
            "open_unit": (lambda: self.pico_status.open_unit, None),
            "pico_setup_verify": (lambda: self.pico_status.pico_setup_verify, None),
            "channel_setup_verify": (lambda: self.pico_status.channel_setup_verify, None),
            "channel_trigger_verify": (lambda: self.pico_status.channel_trigger_verify, None),
            "capture_settings_verify": (lambda: self.pico_status.capture_settings_verify, None),
            "file_name_verify": (lambda: True, None)
        })

    def create_channel_parameter_tree(self):
        """Create channel parameter trees."""
        chan_params = {}
        
        for name in self.dev_conf.channel_names:
            chan_params[name] = self._create_single_channel_tree(name)
        
        return chan_params

    def _create_single_channel_tree(self, channel_name):
        """Create parameter tree for a single channel."""
        channel_attr = f"channel_{channel_name}"
        
        return ParameterTree({
            "channel_id": (
                partial(get_dc_value, self.dev_conf, channel_attr, "channel_id"),
                None,
            ),
            "active": (
                partial(get_dc_value, self.dev_conf, channel_attr, "active"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "active"),
            ),
            "verified": (
                partial(get_dc_value, self.dev_conf, channel_attr, "verified"),
                None,
            ),
            "live_view": (
                partial(get_dc_value, self.dev_conf, channel_attr, "live_view"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "live_view"),
            ),
            "coupling": (
                partial(get_dc_value, self.dev_conf, channel_attr, "coupling"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "coupling"),
            ),
            "range": (
                partial(get_dc_value, self.dev_conf, channel_attr, "range"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "range"),
            ),
            "offset": (
                partial(get_dc_value, self.dev_conf, channel_attr, "offset"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "offset"),
            ),
            "pha_active": (
                partial(get_dc_value, self.dev_conf, channel_attr, "pha_active"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "pha_active"),
            ),
            "PHAToggled": (
                partial(get_dc_value, self.dev_conf, channel_attr, "PHAToggled"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "PHAToggled"),
            ),
            "waveformsToggled": (
                partial(get_dc_value, self.dev_conf, channel_attr, "waveformsToggled"),
                partial(set_dc_chan_value, self.controller, self.dev_conf, channel_attr, "waveformsToggled"),
            ),
        })

    def create_trigger_tree(self):
        """Create trigger parameter tree."""
        return ParameterTree({
            "active": (
                lambda: self.dev_conf.trigger.active,
                partial(set_dc_value, self.controller, self.dev_conf.trigger, "active"),
            ),
            "auto_trigger": (
                lambda: self.dev_conf.trigger.auto_trigger_ms,
                partial(set_dc_value, self.controller, self.dev_conf.trigger, "auto_trigger_ms"),
            ),
            "direction": (
                lambda: self.dev_conf.trigger.direction,
                partial(set_dc_value, self.controller, self.dev_conf.trigger, "direction"),
            ),
            "delay": (
                lambda: self.dev_conf.trigger.delay,
                partial(set_dc_value, self.controller, self.dev_conf.trigger, "delay"),
            ),
            "source": (
                lambda: self.dev_conf.trigger.source,
                partial(set_dc_value, self.controller, self.dev_conf.trigger, "source"),
            ),
            "threshold": (
                lambda: self.dev_conf.trigger.threshold,
                partial(set_dc_value, self.controller, self.dev_conf.trigger, "threshold"),
            ),
        })

    def create_capture_tree(self):
        """Create capture parameter tree."""
        return ParameterTree({
            "pre_trig_samples": (
                lambda: self.dev_conf.capture.pre_trig_samples,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "pre_trig_samples"),
            ),
            "post_trig_samples": (
                lambda: self.dev_conf.capture.post_trig_samples,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "post_trig_samples"),
            ),
            "n_captures": (
                lambda: self.dev_conf.capture.n_captures,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "n_captures"),
            ),
            "capture_time": (
                lambda: self.dev_conf.capture.capture_time,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "capture_time"),
            ),
            "capture_mode": (
                lambda: self.dev_conf.capture.capture_type,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "capture_type"),
            ),
            "capture_delay": (
                lambda: self.dev_conf.capture.capture_delay,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "capture_delay"),
            ),
            "repeat_amount": (
                lambda: self.dev_conf.capture.repeat_amount,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "repeat_amount"),
            ),
            "capture_repeat": (
                lambda: self.dev_conf.capture.capture_repeat,
                partial(set_dc_value, self.controller, self.dev_conf.capture, "capture_repeat"),
            ),
            "max_captures": (lambda: self.pico.rec_caps, None),
            "max_time": (lambda: self.buffer_manager.estimate_max_time(), None)
        })

    def create_mode_tree(self):
        """Create mode parameter tree."""
        return ParameterTree({
            "resolution": (
                lambda: self.dev_conf.mode.resolution,
                partial(set_dc_value, self.controller, self.dev_conf.mode, "resolution"),
            ),
            "timebase": (
                lambda: self.dev_conf.mode.timebase,
                partial(set_dc_value, self.controller, self.dev_conf.mode, "timebase"),
            ),
            "samp_time": (lambda: self.dev_conf.mode.samp_time, None),
        })

    def create_file_tree(self):
        """Create file parameter tree."""
        return ParameterTree({
            "folder_name": (
                lambda: self.dev_conf.file.folder_name,
                partial(set_dc_value, self.controller, self.dev_conf.file, "folder_name"),
            ),
            "file_name": (
                lambda: self.dev_conf.file.file_name,
                partial(set_dc_value, self.controller, self.dev_conf.file, "file_name"),
            ),
            "file_path": (lambda: self.dev_conf.file.file_path, None),
            "curr_file_name": (lambda: self.dev_conf.file.curr_file_name, None),
            "last_write_success": (lambda: self.dev_conf.file.last_write_success, None),
        })

    def create_pha_tree(self):
        """Create PHA parameter tree."""
        return ParameterTree({
            "num_bins": (
                lambda: self.dev_conf.pha.num_bins,
                partial(set_dc_value, self.controller, self.dev_conf.pha, "num_bins"),
            ),
            "lower_range": (
                lambda: self.dev_conf.pha.lower_range,
                partial(set_dc_value, self.controller, self.dev_conf.pha, "lower_range"),
            ),
            "upper_range": (
                lambda: self.dev_conf.pha.upper_range,
                partial(set_dc_value, self.controller, self.dev_conf.pha, "upper_range"),
            ),
        })

    def create_commands_tree(self):
        """Create commands parameter tree."""
        return ParameterTree({
            "run_user_capture": (
                lambda: self.pico_status.flags.user_capture,
                partial(set_dc_value, self.controller, self.pico_status.flags, "user_capture"),
            ),
            "clear_pha": (
                lambda: self.dev_conf.pha.clear_pha,
                partial(set_dc_value, self.controller, self.dev_conf.pha, "clear_pha"),
            )
        })

    def create_flags_tree(self):
        """Create flags parameter tree."""
        return ParameterTree({
            "abort_cap": (
                lambda: self.pico_status.flags.abort_cap,
                partial(set_dc_value, self.controller, self.pico_status.flags, "abort_cap"),
            ),
            "system_state": (lambda: self.pico_status.flags.system_state, None),
        })

    def create_live_view_tree(self):
        """Create live view parameter tree."""
        return ParameterTree({
            "lv_active_channels": (
                lambda: self.buffer_manager.lv_channels_active,
                None,
            ),
            "pha_counts": (lambda: self.buffer_manager.pha_counts.tolist(), None),
            "capture_count": (
                lambda: self.dev_conf.capture_run.live_cap_comp,
                None,
            ),
            "captures_requested": (lambda: self.dev_conf.capture.n_captures, None),
            "lv_data": (lambda: self.buffer_manager.lv_channel_arrays, None),
            "pha_bin_edges": (lambda: self.buffer_manager.bin_edges.tolist(), None),
            "sweep_total": (lambda: self.gpib_config.sweep_points, None),
            "sweep_index": (lambda: self.gpib_config.sweep_index, None),
            "pha_active_channels": (
                lambda: self.buffer_manager.pha_active_channels,
                None,
            ),
            "current_tbdc_time": (lambda: self.pico.elapsed_time, None),
            "current_capture": (lambda: self.controller.dev_conf.capture_run.current_capture, None),
        })

    def create_gpio_tree(self):
        return ParameterTree({
            "capturing": (lambda: self.gpio_config.capture, None),
            "capture_run": (lambda: self.gpio_config.capture_run, self.gpio_config.set_capture_run),
            "enabled": (lambda: self.gpio_config.enabled, None),
            "gpio_captures": (lambda: self.gpio_config.gpio_captures, None),
            "missed_triggers": (lambda: self.gpio_config.missed_triggers, None)
        })

    def build_device_tree(self):
        """Build the complete PicoScope device parameter tree structure."""
        # Create all component trees
        adapter_status = self.create_adapter_status_tree()
        pico_commands = self.create_commands_tree()
        pico_flags = self.create_flags_tree()
        live_view = self.create_live_view_tree()
        gpio_tree = self.create_gpio_tree()
        
        # Create settings tree
        pico_settings = ParameterTree({
            "mode": self.create_mode_tree(),
            "channels": {name: channel for (name, channel) in self.create_channel_parameter_tree().items()},
            "trigger": self.create_trigger_tree(),
            "capture": self.create_capture_tree(),
            "file": self.create_file_tree(),
            "pha": self.create_pha_tree(),
        })

        # Return the complete device parameter tree
        return ParameterTree({
            "status": adapter_status,
            "commands": pico_commands,
            "settings": pico_settings,
            "flags": pico_flags,
            "live_view": live_view,
            "gpio": gpio_tree 
        })
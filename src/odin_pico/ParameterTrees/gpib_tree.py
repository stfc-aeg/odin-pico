from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odin_pico.pico_controller import PicoController

from odin.adapters.parameter_tree import ParameterTree
from odin_pico.Utilities.param_tree import set_dc_value

class GPIBTreeBuilder:
    """Class to build GPIB-related parameter trees."""
    
    def __init__(self, controller:PicoController):
        """Initialise with controller reference and extract GPIB dependencies."""
        self.controller = controller
        self.gpib_config = controller.gpib_config
        
    def create_gpib_tree(self):
        """Create GPIB parameter tree - basic if not available, full if available."""
        # Always include basic GPIB status
        base_tree = {
            "gpib_avail": (lambda: self.controller.gpib_config.avail, None),
            "gpib_control": (
                lambda: self.controller.gpib_config.control_enabled, 
                lambda value: setattr(self.controller.gpib_config, 'control_enabled', value)
            ),
        }
        
        # Add full TEC functionality if available, merge tec tree into base tree
        if self.controller.gpib_config.avail and self.controller.gpib_config.tec_devices:
            base_tree.update(self._create_tec_tree())
        
        return ParameterTree(base_tree)

    def _create_tec_tree(self):
        """Create TEC-specific parameter tree sections."""
        return {
            "available_tecs": (lambda: self.controller.gpib_config.tec_devices, None),
            "selected_tec": (
                lambda: self.controller.gpib_config.selected_tec, 
                lambda value: setattr(self.controller.gpib_config, 'selected_tec', value)
            ),
            "device_control_state": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/device_control_state"
                ) if self.controller.gpib_config.selected_tec else None, 
                lambda value: self.controller.util.iac_set(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/", 
                    {"device_control_state": value}
                ) if self.controller.gpib_config.selected_tec else None
            ),
            "output_state": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/output_state"
                ) if self.controller.gpib_config.selected_tec else None, 
                lambda value: self.controller.util.iac_set(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/", 
                    {"output_state": value}
                ) if self.controller.gpib_config.selected_tec else None
            ),
            "temp_over_state": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/temp_over_state"
                ) if self.controller.gpib_config.selected_tec else None, 
                lambda value: self.controller.util.iac_set(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/", 
                    {"temp_over_state": value}
                ) if self.controller.gpib_config.selected_tec else None
            ),
            "set": self._create_gpib_set_tree(),
            "info": self._create_gpib_info_tree(),
            "temp_sweep": self._create_gpib_temp_sweep_tree()
        }

    def _create_gpib_set_tree(self):
        """Create GPIB set parameter tree."""
        return ParameterTree({
            "temp_target": (
                lambda: self.gpib_config.temp_target,
                lambda v: setattr(self.gpib_config, "temp_target", float(v))
            ),
            "set_temp": (
                lambda: None,
                self.controller.set_temp_single_shot
            ),
            "c_lim": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/set/c_lim_set"
                ) if self.controller.gpib_config.selected_tec else None, 
                lambda value: self.controller.util.iac_set(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/set/c_lim_set", 
                    float(value)
                ) if self.controller.gpib_config.selected_tec else None
            ),
            "v_lim": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/set/v_lim_set"
                ) if self.controller.gpib_config.selected_tec else None, 
                lambda value: self.controller.util.iac_set(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/set/v_lim_set", 
                    float(value)
                ) if self.controller.gpib_config.selected_tec else None
            )
        })

    def _create_gpib_info_tree(self):
        """Create GPIB info parameter tree."""
        return ParameterTree({
            "tec_setpoint": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_setpoint"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
            "tec_volt_lim": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_volt_lim"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
            "tec_curr_lim": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_curr_lim"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
            "tec_current": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_current"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
            "tec_voltage": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_voltage"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
            "tec_power": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_power"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
            "tec_temp_meas": (
                lambda: self.controller.util.iac_get(
                    self.controller.gpib, 
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_temp_meas"
                ) if self.controller.gpib_config.selected_tec else None, None
            ),
        })

    def _create_gpib_temp_sweep_tree(self):
        """Create GPIB temperature sweep parameter tree."""
        return ParameterTree({
            "active": (
                lambda: self.gpib_config.active,
                lambda v: set_dc_value(self.controller, self.gpib_config, "active", v)
            ),
            "t_start": (
                lambda: self.gpib_config.t_start,
                lambda v: set_dc_value(self.controller, self.gpib_config, "t_start", v)
            ),
            "t_end": (
                lambda: self.gpib_config.t_end,
                lambda v: set_dc_value(self.controller, self.gpib_config, "t_end", v)
            ),
            "t_step": (
                lambda: self.gpib_config.t_step,
                lambda v: set_dc_value(self.controller, self.gpib_config, "t_step", v)
            ),
            "tol": (
                lambda: self.gpib_config.tol,
                lambda v: set_dc_value(self.controller, self.gpib_config, "tol", v)
            ),
            "poll_s": (
                lambda: self.gpib_config.poll_s,
                lambda v: set_dc_value(self.controller, self.gpib_config, "poll_s", v)
            ),
        })
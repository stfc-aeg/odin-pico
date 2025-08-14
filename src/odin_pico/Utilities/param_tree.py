from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from odin_pico.pico_controller import PicoController

def get_dc_value(obj, chan_name, attr_name):
    """Retrive values for the live-view settings."""
    try:
        channel_dc = getattr(obj, chan_name)
        return getattr(channel_dc, attr_name, None)
    except AttributeError:
        return None

def set_dc_value(ctrl:PicoController, obj, attr_name, value):
    """Change values for the live-view settings."""
    # Check if PHA needs to be reset
    if (
        (attr_name == "num_bins")
        or (attr_name == "lower_range")
        or (attr_name == "upper_range")
    ):
        ctrl.dev_conf.pha.clear_pha = True

    # Ensure a negative value has not been entered
    if attr_name == "pre_trig_samples" or attr_name == "post_trig_samples" or (
        attr_name == "auto-trigger_ms") or attr_name == "delay" or (
            attr_name == "capture_delay"):
        if value < 0:
            value = value * (-1)

    # Check setting validity
    # Check upper range is not lower than lower range, and vice versa
    if attr_name == "upper_range":
        if value < ctrl.dev_conf.pha.lower_range:
            value = ctrl.dev_conf.pha.lower_range + 1

    if attr_name == "lower_range":
    #     if value < 0:
    #         value = value * (-1)


        if value > ctrl.dev_conf.pha.upper_range:
            value = ctrl.dev_conf.pha.upper_range - 1

    if attr_name == "num_bins" or attr_name == "n_captures" or attr_name == "repeat_amount":
        if value < 1:
            value = 1

    if attr_name == "capture_time":
        if value <= 0:
            value = value * (-1)

    setattr(obj, attr_name, value)

def set_dc_chan_value(ctrl:PicoController, obj, chan_name, attr_name, value):
    """Change values for the individual channel settings."""
    # Ensure the user does not input a negative offset
    # if attr_name == "offset":
    #     if value < 0:
    #         value = value * (-1)

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
    # reset pha if pha params change
    if (
        (attr_name == "num_bins")
        or (attr_name == "lower_range")
        or (attr_name == "upper_range")
    ):
        ctrl.dev_conf.pha.clear_pha = True
        if attr_name == "num_bins":
            ctrl.buffer_manager.reset_pha()
"""Store flags to trigger the controller to complete PicoScope tasks."""

from dataclasses import dataclass


@dataclass
class DeviceFlags:
    verify_all: bool = False
    res_changed: bool = False
    range_changed: bool = False
    user_capture: bool = False
    pico_mem_exceeded: bool = False
    abort_cap: bool = False
    temp_set: bool = False
    temp_reached: bool = False
    system_state: str = "Waiting for connection"
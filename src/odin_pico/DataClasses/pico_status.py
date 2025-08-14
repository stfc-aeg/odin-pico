"""Store settings to represent various status parameters """

import ctypes
from dataclasses import dataclass, field

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

@dataclass
class DeviceStatus:
    open_unit: int = -1
    stop: int = -1
    close: int = -1
    block_check: ctypes.c_int16 = ctypes.c_int16(0)
    block_ready: ctypes.c_int16 = ctypes.c_int16(0)
    pico_setup_verify: int = -1
    pico_setup_complete: int = -1
    channel_setup_verify: int = -1
    channel_setup_complete: int = -1
    channel_trigger_verify: int = -1
    channel_trigger_complete: int = -1
    capture_settings_verify: int = -1
    capture_settings_complete: int = -1
    flags: DeviceFlags = field(default_factory=DeviceFlags)
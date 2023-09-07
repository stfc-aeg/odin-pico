from dataclasses import dataclass, field
import ctypes

from odin_pico.DataClasses.device_flags import DeviceFlags

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
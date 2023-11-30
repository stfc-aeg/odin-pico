from dataclasses import dataclass, field

@dataclass
class DeviceFlags:
    verify_all: bool = False
    res_changed: bool = False
    range_changed: bool = False
    user_capture: bool = False
    pha_capture: bool = False
    pico_mem_exceeded: bool = False
    abort_cap: bool = False
    system_state: str = 'Waiting for connection'
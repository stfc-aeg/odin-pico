import ctypes
from dataclasses import dataclass

@dataclass
class ModeConfig:
    handle: ctypes.c_int16 = ctypes.c_int16(0)
    resolution: int = 1
    timebase: int = 2
    samp_time: int = 0
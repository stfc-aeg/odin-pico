"""Store settings for the PicoScope metadata."""

import ctypes
from dataclasses import dataclass


@dataclass
class MetaDataConfig:
    max_adc: ctypes.c_uint16 = ctypes.c_uint16()
    max_samples: ctypes.c_int32 = ctypes.c_int32()
    total_cap_samples: ctypes.c_int32 = ctypes.c_int32()
    samples_per_seg: ctypes.c_int32 = ctypes.c_int32(0)

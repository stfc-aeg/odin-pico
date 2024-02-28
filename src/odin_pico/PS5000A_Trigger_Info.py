import ctypes


class Trigger_Info(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("status", ctypes.c_uint32),
        ("segmentIndex", ctypes.c_uint32),
        ("triggerIndex", ctypes.c_uint32),
        ("triggerTime", ctypes.c_int64),
        ("timeUnits", ctypes.c_int16),
        ("reserved0", ctypes.c_int16),
        ("timeStampCounter", ctypes.c_uint64),
    ]

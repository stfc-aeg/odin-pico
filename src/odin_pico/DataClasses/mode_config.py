import ctypes
from dataclasses import dataclass, field

from odin_pico.pico_util import PicoUtil


@dataclass
class ModeConfig:
    handle: ctypes.c_int16 = ctypes.c_int16(0)
    timebase: int = 2
    samp_time: int = 0
    _resolution: int = 1

    util: PicoUtil = field(default_factory=PicoUtil)

    @property
    def resolution(self) -> int:
        return self._resolution

    @resolution.setter
    def resolution(self, value: int):
        if value in self.util.ps_resolution:
            self._resolution = value

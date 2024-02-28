from dataclasses import dataclass, field

from odin_pico.pico_util import PicoUtil


@dataclass
class TriggerConfig:
    active: bool = True
    threshold: int = 0
    delay: int = 0
    auto_trigger_ms: int = 0
    _source: int = 0
    _direction: int = 2

    util: PicoUtil = field(default_factory=PicoUtil)

    @property
    def source(self) -> int:
        return self._source

    @source.setter
    def source(self, value: int):
        if value in self.util.ps_channel:
            self._source = value

    @property
    def direction(self) -> int:
        return self._direction

    @direction.setter
    def direction(self, value: int):
        if value in self.util.ps_direction:
            self._direction = value

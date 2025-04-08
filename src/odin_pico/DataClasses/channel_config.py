"""Store settings for each PicoScope channel."""

from dataclasses import dataclass, field

from odin_pico.pico_util import PicoUtil


@dataclass
class ChannelConfig:
    channel_id: int
    name: str
    active: bool = False
    verified: bool = False
    live_view: bool = False
    offset: float = 0.0
    _coupling: int = 1
    _range: int = 0
    pha_active: bool = False

    util: PicoUtil = field(default_factory=PicoUtil)

    @staticmethod
    def default_channel_configs():
        return {
            name: ChannelConfig(id, name)
            for (id, name) in enumerate(["a", "b", "c", "d"])
        }

    @property
    def coupling(self) -> int:
        return self._coupling

    @coupling.setter
    def coupling(self, value: int):
        if value in self.util.ps_coupling:
            self._coupling = value
        else:
            print("Value passed to channel_config for coupling out of bounds")

    @property
    def range(self) -> int:
        return self._range

    @range.setter
    def range(self, value: int):
        if value in self.util.ps_range:
            self._range = value
        else:
            print("Value passed to channel_config for range out of bounds")

    def custom_asdict(self):
        """Convert the object to a dictionary, using property names instead of private attributes."""
        #use property names for source and direction and not private attributes
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "active": self.active,
            "verified": self.verified,
            "live_view": self.live_view,
            "offset": self.offset,
            "coupling": self.coupling,  # Uses the property, not _coupling
            "range": self.range,  # Uses the property, not _range
            "pha_active": self.pha_active,
        }
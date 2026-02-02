"""File to provide all the seperate dataclasses that represent the configurations for different sections of the PicoScope codebase"""

import ctypes
from dataclasses import dataclass, field, fields
from odin_pico.Utilities.pico_util import PicoUtil

util = PicoUtil()

@dataclass
class PHAConfig:
    clear_pha:bool = False
    num_bins: int = 1024
    lower_range: int = 0
    upper_range: int = 0

@dataclass
class MetaDataConfig:
    max_adc: ctypes.c_uint16 = ctypes.c_uint16()
    max_samples: ctypes.c_int32 = ctypes.c_int32()
    total_cap_samples: ctypes.c_int32 = ctypes.c_int32()
    samples_per_seg: ctypes.c_int32 = ctypes.c_int32(0)

@dataclass
class CaptureRunConfig:
    caps_comp: int = 0
    caps_in_run: int = 0
    caps_remaining: int = 0
    caps_max: int = 0
    live_cap_comp: int = 100
    caps_collected: int = 0
    #current capture repeat iterator
    current_capture: int = 0

    def reset(self):
        for field in fields(self):
            setattr(self, field.name, field.default)

@dataclass
class CaptureConfig:
    capture_time: float = 3.0
    caps_in_cycle: int = 100
    pre_trig_samples: int = 5000
    post_trig_samples: int = 5000
    n_captures: int = 50
    capture_type: bool = False
    capture_delay: int = 0
    capture_repeat: bool = False
    repeat_amount: int = 1

@dataclass
class ModeConfig:
    handle: ctypes.c_int16 = ctypes.c_int16(0)
    timebase: int = 2
    samp_time: int = 0
    _resolution: int = 1

    @property
    def resolution(self) -> int:
        return self._resolution

    @resolution.setter
    def resolution(self, value: int):
        if value in util.ps_resolution:
            self._resolution = value

@dataclass
class FileConfig:
    file_name: str = ""
    folder_name: str = ""
    _file_path: str = ""
    curr_file_name: str = ""
    last_write_success: bool = False
    temp_suffix: str = None   # e.g. "_25-0c"
    repeat_suffix: str = None   # e.g. "_3"
    trig_suffix: str = ""   # e.g. "0001"
    available_space: str = ""

    @property
    def file_path(self) -> str:
        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        self._file_path = value

@dataclass
class TriggerConfig:
    active: bool = True
    threshold: int = 0
    delay: int = 0
    auto_trigger_ms: int = 0
    _source: int = 0
    _direction: int = 2

    @property
    def source(self) -> int:
        return self._source

    @source.setter
    def source(self, value: int):
        if value in util.ps_channel:
            self._source = value

    @property
    def direction(self) -> int:
        return self._direction

    @direction.setter
    def direction(self, value: int):
        if value in util.ps_direction:
            self._direction = value
    active: bool = True
    threshold: int = 0
    delay: int = 0
    auto_trigger_ms: int = 0
    _source: int = 0
    _direction: int = 2

    def custom_asdict(self):
        """
        Convert the dataclass to a dictionary, using property names where applicable
        instead of private attributes.
        """
        #use property names for source and direction and not private attributes
        dict = {
            "active": self.active,
            "threshold": self.threshold,
            "delay": self.delay,
            "auto_trigger_ms": self.auto_trigger_ms,
            "source": self.source,  # Uses the property, not _source
            "direction": self.direction,  # Uses the property, not _direction
        }
        return dict 
    
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
    PHAToggled: bool = True
    waveformsToggled: bool = True

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
        if value in util.ps_coupling:
            self._coupling = value
        else:
            print("Value passed to channel_config for coupling out of bounds")

    @property
    def range(self) -> int:
        return self._range

    @range.setter
    def range(self, value: int):
        if value in util.ps_range:
            self._range = value
        else:
            print("Value passed to channel_config for range out of bounds")

    def custom_asdict(self):
        """Convert the object to a dictionary, using property names instead of private attributes."""
        # use property names for source and direction and not private attributes
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
            "PHAToggled": self.PHAToggled,
            "waveformsToggled": self.waveformsToggled,
        }
    

@dataclass
class DeviceConfig:
    preview_channel: int = 0
    config_folder_path: str = "/tmp/configs/"
    capture_folder_path: str = "/tmp/captures/"
    channel_names: list[str] = field(default_factory=list)
    mode: ModeConfig = field(default_factory=ModeConfig)
    trigger: TriggerConfig = field(default_factory=TriggerConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    capture_run: CaptureRunConfig = field(default_factory=CaptureRunConfig)
    meta_data: MetaDataConfig = field(default_factory=MetaDataConfig)
    file: FileConfig = field(default_factory=FileConfig)
    pha: PHAConfig = field(default_factory=PHAConfig)

    def __post_init__(self):
        for name, channel in ChannelConfig.default_channel_configs().items():
            setattr(self, f"channel_{name}", channel)
            self.channel_names.append(name)

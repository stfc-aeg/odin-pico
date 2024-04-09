"""Store settings for a PicoScope capture."""

from dataclasses import dataclass


@dataclass
class CaptureConfig:
    capture_time: float = 3.0
    caps_in_cycle: int = 100
    pre_trig_samples: int = 0
    post_trig_samples: int = 10000
    n_captures: int = 50
    capture_type: bool = False
    capture_delay: int = 0
    capture_repeat: bool = False
    repeat_amount: int = 1

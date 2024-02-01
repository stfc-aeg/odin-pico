from dataclasses import dataclass

@dataclass
class CaptureConfig:
    time_based: bool = False
    sample_time: int = 10
    caps_in_cycle: int = 100
    pre_trig_samples: int = 0
    post_trig_samples: int = 100000
    n_captures: int = 3
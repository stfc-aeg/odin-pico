from dataclasses import dataclass

@dataclass
class CaptureConfig:
    pre_trig_samples: int = 0
    post_trig_samples: int = 100000
    n_captures: int = 3
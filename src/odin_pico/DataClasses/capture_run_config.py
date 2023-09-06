from dataclasses import dataclass

@dataclass
class CaptureRunConfig:
    caps_comp: int = 0
    caps_in_run: int = 0
    caps_remaining: int = 0
    caps_max: int = 0
    live_cap_comp: int = 0
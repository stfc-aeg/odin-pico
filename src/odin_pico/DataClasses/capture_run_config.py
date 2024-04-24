"""Store settings for a PicoScope capture run."""

from dataclasses import dataclass, fields


@dataclass
class CaptureRunConfig:
    caps_comp: int = 0
    caps_in_run: int = 0
    caps_remaining: int = 0
    caps_max: int = 0
    live_cap_comp: int = 100

    def reset(self):
        for field in fields(self):
            setattr(self, field.name, field.default)

"""Store settings for the Pulse Height Analysis."""

from dataclasses import dataclass

@dataclass
class PHAConfig:
    num_bins: int = 1024
    lower_range: int = 0
    upper_range: int = 20000

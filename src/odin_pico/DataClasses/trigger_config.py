from dataclasses import dataclass

@dataclass
class TriggerConfig:
    active: bool = True
    source: int = 0
    threshold: int = 0
    direction: int = 2
    delay: int = 0
    auto_trigger_ms: int = 0
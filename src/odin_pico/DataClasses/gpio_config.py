from dataclasses import dataclass

@dataclass
class GPIOConfig:

    capture: bool = False
    capture_run: int = 56
    enabled: bool = False
    gpio_captures: int = 0
    identity: str = ""
    missed_triggers: int = 0

    def set_capture_run(self, value):
        self.capture_run = value
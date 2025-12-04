from dataclasses import dataclass

@dataclass
class GPIOConfig:

    active: bool = False
    capture: bool = False
    capture_run: int = 10
    enabled: bool = False
    gpio_captures: int = 0
    identity: str = ""
    listening: bool = False
    missed_triggers: int = 0
    unexpected_triggers: int = 0

    def set_active(self, value):
        self.active = value

    def set_capture_run(self, value):
        self.capture_run = value

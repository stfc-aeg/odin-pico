from dataclasses import dataclass, field

@dataclass
class GPIBConfig:

    avail: bool = False
    control_enabled: bool = False
    tec_devices: list[str] = field(default_factory=list)
    selected_tec: str = ""
    temp_setpoint: float = 0.0 #remove?
    temp_target: float = 0.0
    voltage_limit: float = 0.0
    current_limit: float = 0.0
    
    active: bool = False   
    t_start: float = 0.0
    t_end:   float = 0.0
    t_step:  float =  0.0
    tol:     float = 0.1
    poll_s:  float = 0.25
    sweep_points: int = 0   # total points in this sweep
    sweep_index:  int = 0   # 0-based index of the current point
    stability_time: float = 5          # Time in seconds to check for stability
    max_wait_time: float = 300.0          # Maximum wait time in seconds
    min_stability_readings: int = 5       # Minimum readings regardless of time
    max_stability_readings: int = 100     # Lenght of reading lsit    
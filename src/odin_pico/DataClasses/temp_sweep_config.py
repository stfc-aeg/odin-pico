from dataclasses import dataclass

@dataclass
class TempSweepConfig:
    active: bool  = False   
    t_start: float = 0.0
    t_end:   float = 0.0
    t_step:  float =  0.0
    tol:     float = 0.1
    poll_s:  float = 0.25
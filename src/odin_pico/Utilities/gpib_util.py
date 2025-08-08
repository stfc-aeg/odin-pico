from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from odin_pico.pico_controller import PicoController

import logging
import time
import re
from collections import deque


class GPIBUtil:
    """Class containing GPIB and temperature control functions."""
    
    def __init__(self, controller:PicoController):
        """Initialize with controller reference."""
        self.controller = controller

    def wait_for_tec(self, target: float, tol: float):
        """
        Simple temperature stability check with basic logging.
        Waits for temperature to remain stable within tolerance for specified time.
        """
        sweep_config = self.controller.gpib_config

        # Simple time-based calculation
        stability_readings = int(sweep_config.stability_time / sweep_config.poll_s)
        errors = deque(maxlen=stability_readings)
        
        start_time = time.time()
        logging.info(f"[TEC] Waiting for {target:.2f}°C ± {tol:.2f}°C")  
        reading_count = 0
        
        while not self.controller.pico_status.flags.abort_cap:
            # Get current temperature
            meas = self.controller.util.iac_get(
                self.controller.gpib, 
                f"devices/{self.controller.gpib_config.selected_tec}/info/tec_temp_meas"
            )
            if meas is None:
                logging.error("[TEC] Failed to read temperature")
                break
                
            # Calculate error and add to rolling window
            error = meas - target
            errors.append(error)
            reading_count += 1
            
            if reading_count % 10 == 0:
                elapsed = time.time() - start_time
                mean_error = sum(abs(e) for e in errors) / len(errors)
                logging.debug(f"[TEC] Current: {meas:.2f}°C, Avg error: ±{mean_error:.3f}°C "
                            f"(readings: {len(errors)}/{stability_readings}, elapsed: {elapsed:.1f}s)")
            
            # Check for stability once we have enough readings
            if len(errors) >= stability_readings:
                mean_error = sum(abs(e) for e in errors) / len(errors)
                
                if mean_error <= tol:
                    elapsed_time = time.time() - start_time
                    actual_stability_time = len(errors) * sweep_config.poll_s
                    logging.info(f"[TEC] Temperature stable at {meas:.2f}°C "
                                f"(±{mean_error:.3f}°C over {actual_stability_time:.1f}s, "
                                f"total time: {elapsed_time:.1f}s)")
                    return
            time.sleep(sweep_config.poll_s)

    def temp_range(self, start, end, step):
        """
        Return a list of temperatures in equal increments, direction is 
        inferred from start and end.
        """
        if step == 0 or start == end:
            return [start]

        step = abs(step)  # ignore sign the user gave
        direction = 1 if end >= start else -1
        temps = [start]
        current = start

        while True:
            next_val = current + direction * step
            # Would the next step cross the end value?
            if (direction == 1 and next_val >= end) or \
               (direction == -1 and next_val <= end):
                break
            temps.append(next_val)
            current = next_val

        if temps[-1] != end:
            temps.append(end)

        logging.debug(f"returning temps: {temps}")
        return temps

    def temp_suffix(self, T: float) -> str:
        """
        Return a filename-safe suffix like '_25-0c' or '_-5-0c'
        """
        s = f"{T:.1f}".replace(".", "-")
        return f"_{s}c"

    def clean_base_fname(self) -> str:
        """
        Return the users current file name without .hdf5 and other suffixes    
        """
        name = self.controller.dev_conf.file.file_name
        if name.endswith(".hdf5"):
            name = name[:-5]

        # strip "…_<digits>"  (repeat suffix)
        name = re.sub(r"_\d+$", "", name)

        # strip "…_<±number>[ - number]c"  (temperature suffix)
        name = re.sub(r"_-?\d+(?:-\d+)?c$", "", name)

        return name.rstrip("_")
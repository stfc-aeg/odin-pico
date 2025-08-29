from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from odin_pico.pico_controller import PicoController

import logging
import time
import re
from collections import deque


class GPIBUtil:
    """Class containing GPIB and temperature related functions."""
    
    def __init__(self, controller:PicoController):
        """Initialise with controller reference."""
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

    def run_temperature_sweep(self):
        """
        Iterate over every temperature in the listeven in SIM mode
        and acquire data.  A guard flag prevents any single capture from
        setting `abort_cap` and killing the rest of the sweep.
        """
        sweep = self.controller.gpib_config
        if not sweep.active:
            return

        temps    = self.temp_range(sweep.t_start, sweep.t_end, sweep.t_step)
        self.controller.gpib_config.sweep_points = len(temps)
        logging.info(f"[TEC-sweep] Set-points: {temps}")

        base_fname = self.clean_base_fname()

        # local flag so abort in one capture doesn’t cancel the sweep
        sweep_abort = False

        for idx, T in enumerate(temps):
            self.controller.gpib_config.sweep_index  = idx
            logging.debug(f"Current temp sweep: {self.controller.gpib_config.sweep_index}")
            if sweep_abort:
                break

            # Set temperature on Tec
            if self.controller.simulate:
                logging.info(f"[SIM] TEC set-point {T:.2f} °C")
            else:
                self.controller.util.iac_set(
                    self.controller.gpib,
                    f"devices/{self.controller.gpib_config.selected_tec}/set/temp_set",
                    float(T)
                )
            self.controller.buffer_manager.temp_set_last = T

            # ── 2) wait / mock wait until stable ────────────────────────────

            if self.controller.simulate:
                time.sleep(sweep.poll_s)
                self.controller.buffer_manager.temp_meas_last = T
            else:
                self.wait_for_tec(T, sweep.tol)
                self.controller.buffer_manager.temp_meas_last = self.controller.util.iac_get(
                    self.controller.gpib,
                    f"devices/{self.controller.gpib_config.selected_tec}/info/tec_temp_meas")
                
            self.controller.dev_conf.file.temp_suffix = str(self.temp_suffix(T))

            # reset abort flag before each capture; if *this* capture sets it,
            # finish the file and then abandon the remaining temps
            self.controller.pico_status.flags.abort_cap = False

            try:
                if self.controller.dev_conf.capture.capture_type:     # time-based
                    self.controller.tb_capture()
                else:                                      # fixed-count
                    self.controller.user_capture(True)
            except Exception as e:
                logging.error(f"Capture failed at {T}°C: {e}")
                sweep_abort = True

        # restore original file_name
        self.controller.dev_conf.file.file_name = base_fname + ".hdf5"
    
        # clear temperature suffix and reset sweep index to 0
        self.controller.dev_conf.file.temp_suffix = None
        self.controller.gpib_config.sweep_points = 0
        self.controller.gpib_config.sweep_index  = 0 

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
    
    
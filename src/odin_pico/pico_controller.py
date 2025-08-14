"""File to control the PicoScope processing."""

import logging
import math
import re
import time
from concurrent import futures
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.concurrent import run_on_executor

from odin_pico.analysis import PicoAnalysis
from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.pico_config import DeviceConfig
from odin_pico.DataClasses.gpib_config import GPIBConfig
from odin_pico.DataClasses.pico_status import DeviceStatus

from odin_pico.file_writer import FileWriter
from odin_pico.pico_device import PicoDevice
from odin_pico.Utilities.controller_util import ControllerUtil
from odin_pico.Utilities.pico_util import PicoUtil

from odin_pico.ParameterTrees.gpib_tree import GPIBTreeBuilder
from odin_pico.ParameterTrees.pico_tree import PicoTreeBuilder

class PicoController:
    """Class which holds parameter trees and manages the PicoScope capture process."""
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, loop, path, max_caps, simulate):
        """Initialise the PicoController Class."""
        # Threading lock and control variables
        self.update_loop_active = loop
        self.simulate = simulate

        # Objects for handling configuration, status and utilities
        self.dev_conf = DeviceConfig()
        self.gpib_config = GPIBConfig()
        self.pico_status = DeviceStatus()
        self.util = PicoUtil()
        self.ctrl_util = ControllerUtil(self)

        # Initialise objects to represent different system components
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf, self.buffer_manager, self.pico_status)
        self.analysis = PicoAnalysis(
            self.dev_conf, self.buffer_manager, self.pico_status
        )
        self.pico = PicoDevice(max_caps, self.dev_conf, self.pico_status,
                               self.buffer_manager, self.analysis, self.file_writer)
        
        # Initialise parameter tree to None, is built in initialize_adapters with access to other adapters
        self.param_tree = None
        self.dev_conf.file.file_path = path

        if self.update_loop_active:
            self.update_loop()

        # Set initial state of the verification system
        self.ctrl_util.verify_settings()

    def initialize_adapters(self, adapters):
        """Get access to all of the other adapters and build complete parameter tree."""
        try:
            self.gpib = adapters['gpib'] if adapters else None
        except:
            self.gpib = None
        try:
            if self.gpib:
                devices = self.util.iac_get(self.gpib, "devices")
                self.gpib_config.tec_devices = [name for name, info in devices.items()
                    if info.get("type") == "K2510"]

                self.gpib_config.avail = self.ctrl_util.verify_gpib_avail()

                if self.gpib_config.tec_devices:
                    self.gpib_config.selected_tec = self.gpib_config.tec_devices[0]

            # instaniate the parametertree builder classes
            pico_tree_builder = PicoTreeBuilder(self)
            gpib_tree_builder = GPIBTreeBuilder(self)
            
            # Build both device and GPIB trees
            device_tree = pico_tree_builder.build_device_tree()
            gpib_tree = gpib_tree_builder.create_gpib_tree()
            
            # Create the complete parameter tree
            self.param_tree = ParameterTree({
                "device": device_tree,
                "gpib": gpib_tree
            })
        except Exception as e:
            logging.error(e)

    def run_capture(self):
        """Tell the picoscope to collect and return data."""

        # if a single-shot temperature has been set, wait for tec to stablise
        if self.pico_status.flags.temp_set and self.gpib_config.control_enabled:
            self.pico_status.flags.system_state = "Waiting for TEC to stabilise"
            while self.pico_status.flags.temp_set and not self.pico_status.flags.abort_cap:
                time.sleep(0.1)
                logging.debug("waiting for temp")
            # now temp_reached=True
            # reset abort flag if its set
            self.pico_status.flags.abort_cap = False

        # clear the temperature reached flag
        if self.pico_status.flags.temp_reached:
            self.pico_status.flags.temp_reached = False
            
        self.ctrl_util.calc_samp_time()

        if self.pico_status.flags.verify_all:
            self.ctrl_util.check_res()

            # Check if user has requested a capture
            if self.pico_status.flags.user_capture:
                if self.file_writer.check_file_name():

                    self.file_writer.file_error = False

                    # Check if user has requested the capture to be repeated
                    if self.dev_conf.capture.capture_repeat:
                        cap_loop = self.dev_conf.capture.repeat_amount
                        delay = self.dev_conf.capture.capture_delay
                    else:
                        cap_loop = 1
                        delay = 0

                    for capture_run in range(cap_loop):

                        if cap_loop > 1:
                            self.dev_conf.file.repeat_suffix = "_" + str((capture_run+1))
                        # reset abort flag if its been set by TB capture
                        self.pico_status.flags.abort_cap = False
                        self.buffer_manager.reset_pha()
                        self.dev_conf.capture_run.current_capture = capture_run

                        logging.debug(f"current capture repeat: {self.dev_conf.capture_run.current_capture}")

                        # Complete a capture run, based on capture number
                        if not self.dev_conf.capture.capture_type:
                            if not self.pico_status.flags.abort_cap:
                                # TEC-sweep
                                if (self.gpib_config.active and
                                    self.gpib_config.control_enabled and
                                    self.gpib_config.avail):
                                    self.run_temperature_sweep()
                                else:
                                    self.user_capture(True)
                        else:
                            self.buffer_manager.reset_pha()

                            # Complete a capture run, for a pre-determined amount of time
                            if not self.pico_status.flags.abort_cap:
                                # TEC-sweep
                                if (self.gpib_config.active and
                                    self.gpib_config.control_enabled and
                                    self.gpib_config.avail):
                                    self.run_temperature_sweep()
                                else:
                                    self.tb_capture()
                        
                        # Delay between capture runs, if requested by user
                        if capture_run != (cap_loop - 1):
                            self.pico_status.flags.system_state = ("Delay Between Captures")
                            start_time = time.time()
                            logging.debug("Entered delay")
                            while (time.time() - start_time) < delay:
                                if self.pico_status.flags.abort_cap:
                                    delay = 0
                                logging.debug("Delaying")
                                time.sleep(0.1)

                        # Change system state, depends on if capture was repeated
                        if (capture_run + 1) == cap_loop:
                            self.current_time = 0

                    self.dev_conf.capture_run.current_capture = 0
                    self.pico_status.flags.user_capture = False
                    self.pico_status.flags.abort_cap = False
                    self.dev_conf.file.repeat_suffix = None

                else:
                    self.file_writer.file_error = True
                    self.pico_status.flags.system_state = (
                        "File Name Empty or Already Exists")
                    self.pico_status.flags.user_capture = False

            # If user hasn't requested a capture, complete a LV capture run
            else:
                if not self.file_writer.file_error:
                    self.pico_status.flags.system_state = "Collecting LV Data"
                self.pico.calc_max_caps()
                self.user_capture(False)
                self.pico_status.flags.abort_cap = False

        if (self.pico_status.open_unit == 0) and (
            self.pico_status.flags.verify_all is False
        ):
            self.pico_status.flags.system_state = "Connected to PicoScope, Idle"

    def user_capture(self, save_file):
        """Run the appropriate steps for a set of captures."""
        # Identify whether the capture is a user capture or just for LV
        if save_file:
            captures = self.dev_conf.capture.n_captures
        else:
            captures = 2
            
        self.ctrl_util.set_capture_run_limits()
        
        #set caps_remaining for liveview mode
        if not save_file:
            self.dev_conf.capture_run.caps_remaining = 2
            
        self.ctrl_util.set_capture_run_length()
    
        # checks run_setup completes successfully, calls it with captures if save_file is not true
        if self.pico.run_setup() if save_file else self.pico.run_setup(captures):
            while self.dev_conf.capture_run.caps_comp < captures:
                if not self.pico_status.flags.abort_cap:
                    self.ctrl_util.set_capture_run_length()
                    self.capture_run()
                    self.dev_conf.capture_run.caps_remaining -= (
                        self.dev_conf.capture_run.caps_in_run
                    )
                else:
                    self.dev_conf.capture_run.caps_comp = captures

            # Saves captures to a file, if requested
            if save_file:
                self.file_writer.write_hdf5()

        self.dev_conf.capture_run.reset()

    def capture_run(self):
        """Run the necessary steps for a capture."""
        # Run the scope, and update the captures completed
        self.pico.assign_pico_memory()
        self.pico.run_block()
        self.dev_conf.capture_run.caps_comp += self.pico.seg_caps * len(
            self.buffer_manager.active_channels
        )

        # Process the data, for the purposes of LV and PHA
        if not self.pico_status.flags.abort_cap:
            self.buffer_manager.save_lv_data()
            self.analysis.pha_one_peak()

    def tb_capture(self):
        """
        """
        # validate this method of calculating max captures!
        self.ctrl_util.set_capture_run_limits()
        self.dev_conf.capture_run.caps_in_run = int(self.dev_conf.capture_run.caps_max/2)
        self.pico.run_time_based_capture(
            self.dev_conf.capture.capture_time
            )
        self.file_writer.write_hdf5(write_accumulated=True)
        self.buffer_manager.clear_arrays()
        self.pico_status.flags.abort_cap = False
   
    def run_temperature_sweep(self):
        """
        Iterate over every temperature in the listeven in SIM mode
        and acquire data.  A guard flag prevents any single capture from
        setting `abort_cap` and killing the rest of the sweep.
        """
        sweep = self.gpib_config
        if not sweep.active:
            return

        temps    = self.ctrl_util.temp_range(sweep.t_start, sweep.t_end, sweep.t_step)
        self.gpib_config.sweep_points = len(temps)
        logging.info(f"[TEC-sweep] Set-points: {temps}")

        base_fname = self.ctrl_util.clean_base_fname()

        # local flag so abort in one capture doesn’t cancel the sweep
        sweep_abort = False

        for idx, T in enumerate(temps):
            self.gpib_config.sweep_index  = idx
            logging.debug(f"Current temp sweep: {self.gpib_config.sweep_index}")
            if sweep_abort:
                break

            # Set temperature on Tec
            if self.simulate:
                logging.info(f"[SIM] TEC set-point {T:.2f} °C")
            else:
                self.util.iac_set(
                    self.gpib,
                    f"devices/{self.gpib_config.selected_tec}/set/temp_set",
                    float(T)
                )
            self.buffer_manager.temp_set_last = T

            # ── 2) wait / mock wait until stable ────────────────────────────

            if self.simulate:
                time.sleep(sweep.poll_s)
                self.buffer_manager.temp_meas_last = T
            else:
                self.ctrl_util.wait_for_tec(T, sweep.tol)
                self.buffer_manager.temp_meas_last = self.util.iac_get(
                    self.gpib,
                    f"devices/{self.gpib_config.selected_tec}/info/tec_temp_meas")
                
            # self.dev_conf.file.file_name = (
            #     base_fname + self.ctrl_util.temp_suffix(T)
            # )
            self.dev_conf.file.temp_suffix = str(self.ctrl_util.temp_suffix(T))

            # reset abort flag before each capture; if *this* capture sets it,
            # finish the file and then abandon the remaining temps
            self.pico_status.flags.abort_cap = False

            try:
                if self.dev_conf.capture.capture_type:     # time-based
                    self.tb_capture()
                else:                                      # fixed-count
                    self.user_capture(True)
            except Exception as e:
                logging.error(f"Capture failed at {T}°C: {e}")
                sweep_abort = True

        # restore original file_name
        self.dev_conf.file.file_name = base_fname + ".hdf5"
    
        # clear temperature suffix and reset sweep index to 0
        self.dev_conf.file.temp_suffix = None
        self.gpib_config.sweep_points = 0
        self.gpib_config.sweep_index  = 0 

    def set_temp_single_shot(self, _=None):
        """
        Called when the user clicks /gpib/set/set_temp.
        Reads temp_target and kicks off the background wait.
        """
        T = self.gpib_config.temp_target
        self.pico_status.flags.temp_set     = True
        self.pico_status.flags.temp_reached = False
        self.pico_status.flags.system_state = f"Setting TEC {T:.2f} °C"
        self._bg_set_and_wait(T)

    @run_on_executor
    def _bg_set_and_wait(self, T: float):
        """
        Background thread:
        a) write the setpoint
        b) wait_for_tec until stable
        c) flip flags & update status
        """
        # a)
        try:
            logging.debug(f"Temp : {T}")
            self.util.iac_set(self.gpib,
                            f"devices/{self.gpib_config.selected_tec}/set",
                            {"temp_set": float(T)})
            val = self.util.iac_get(
                self.gpib,
                f'devices/{self.gpib_config.selected_tec}/set/temp_set'
            )
            logging.debug(f"iac_get returned: {val}")
        except Exception as e:
            logging.error(e)
        # b)
        self.ctrl_util.wait_for_tec(T, self.gpib_config.tol)
            # c)
        self.pico_status.flags.temp_set     = False
        self.pico_status.flags.temp_reached = True

        
    ##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        """Execute thread, responsible for calling the run_capture function at timed intervals."""
        while self.update_loop_active:
            #logging.debug(f"temp target : {(self.gpib_config.temp_target)}")
            self.run_capture()
            time.sleep(0.2)

    def set_update_loop_state(self, state=bool):
        """Set the state of the update_loop in the executor thread."""
        self.update_loop_active = state

    def cleanup(self):
        """Responsible for ensuring the picoscope is closed cleanly when the adapter is shutdown."""
        self.set_update_loop_state(False)
        self.pico_status.flags.abort_cap = True
        self.pico.stop_scope()
        logging.debug("Stopping PicoScope services and closing device")

    def get(self, path):
        """Get the parameter tree."""
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree."""
        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise PicoControllerError(e)
        self.ctrl_util.verify_settings()

class PicoControllerError(Exception):
    pass

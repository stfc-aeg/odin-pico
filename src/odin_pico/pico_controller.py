"""File to control the PicoScope processing."""

import logging
import math
import re
import time
import threading
from concurrent import futures
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.concurrent import run_on_executor

from odin_pico.analysis import PicoAnalysis
from odin_pico.buffer_manager import BufferManager
from odin_pico.DataClasses.pico_config import DeviceConfig
from odin_pico.DataClasses.gpib_config import GPIBConfig
from odin_pico.DataClasses.gpio_config import GPIOConfig
from odin_pico.DataClasses.pico_status import DeviceStatus

from odin_pico.file_writer import FileWriter
from odin_pico.pico_device import PicoDevice
from odin_pico.Utilities.controller_util import ControllerUtil
from odin_pico.Utilities.pico_util import PicoUtil
from odin_pico.Utilities.gpib_util import GPIBUtil

from odin_pico.ParameterTrees.gpib_tree import GPIBTreeBuilder
from odin_pico.ParameterTrees.pico_tree import PicoTreeBuilder

class PicoController:
    """Class which holds parameter trees and manages the PicoScope capture process."""
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, loop, path, disk):
        """Initialise the PicoController Class."""

        # Threading lock and control variables
        self.update_loop_active = loop

        # Objects for handling configuration, status and utilities
        self.dev_conf = DeviceConfig()
        self.gpib_config = GPIBConfig()
        self.gpio_config = GPIOConfig()
        self.pico_status = DeviceStatus()
        self.util = PicoUtil()
        self.gpib_util = GPIBUtil(self)
        self.ctrl_util = ControllerUtil(self)

        # Initialise objects to represent different system components
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(disk, self.dev_conf, self.buffer_manager, self.pico_status)
        self.analysis = PicoAnalysis(
            self.dev_conf, self.buffer_manager, self.pico_status
        )
        self.pico = PicoDevice(disk, self.dev_conf, self.pico_status,
                               self.buffer_manager, self.analysis, self.file_writer, self.gpio_config)
        
        # Initialise parameter tree to None, is built in initialize_adapters with access to other adapters
        self.param_tree = None
        self.dev_conf.file.file_path = path
        self.trig_rate_hz = 0.0
        self.cap_times = []

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
            self.comms = adapters['triggering'] if adapters else None
            self.trigger_controller = self.comms.get_controller()
            self.trigger_controller.register_event(self.trigger_received)
            self.gpio_config.reply_method = self.trigger_controller.get_reply_method()
            self.gpio_config.enabled = True
        except Exception as e:
            self.comms = None
        
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

    def trigger_received(self, identity):

        if self.gpio_config.listening:
            if self.gpio_config.capture:
                self.gpio_config.missed_triggers += 1
                self.gpio_config.gpio_captures += 1
                logging.warning(f"Trigger missed: {self.gpio_config.gpio_captures}")
                return

            self.gpio_config.gpio_captures += 1
            self.dev_conf.file.trig_suffix = f"_{self.gpio_config.gpio_captures:04d}"
            self.gpio_config.identity = identity
            self.gpio_config.capture = True
        else:
            self.gpio_config.unexpected_triggers += 1

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
            if self.pico_status.flags.user_capture | self.gpio_config.capture:
                if self.file_writer.check_file_name():

                    if not self.gpio_config.capture:
                        self.cap_times = []
                        self.file_writer.file_times = []

                    self.file_writer.file_error = False

                    # Check if user has requested the capture to be repeated
                    if self.dev_conf.capture.capture_repeat:
                        cap_loop = self.dev_conf.capture.repeat_amount
                        delay = self.dev_conf.capture.capture_delay
                    else:
                        cap_loop = 1
                        delay = 0

                    for capture_run in range(cap_loop):
                        if not(self.update_loop_active):
                            return

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
                                    self.gpib_util.run_temperature_sweep()
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
                                    self.gpib_util.run_temperature_sweep()
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
                    self.file_writer.calc_disk_space()

                    if self.gpio_config.capture:
                        if self.gpio_config.gpio_captures == self.gpio_config.capture_run:
                            if self.gpio_config.missed_triggers != 0:
                                logging.warning(f"Trigger run complete. Triggers missed: {self.gpio_config.missed_triggers}")
                            self.set_listening(False)
                            self.gpio_config.gpio_captures = 0
                            self.dev_conf.file.trig_suffix = ""

                        self.gpio_config.capture = False
                        self.gpio_config.reply_method(self.gpio_config.identity)
                        self.pico_status.flags.system_state = f"Listening. Captures completed: {self.gpio_config.gpio_captures}"

                else:
                    self.file_writer.file_error = True
                    self.pico_status.flags.system_state = (
                        "File Name Empty or Already Exists")
                    self.pico_status.flags.user_capture = False

            # If user hasn't requested a capture, complete a LV capture run
            else:
                if not self.file_writer.file_error and not self.gpio_config.listening and self.pico_status.open_unit == 0:
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
            captures = 5
            
        self.ctrl_util.set_capture_run_limits()
        
        # Set caps_remaining for liveview mode
        if not save_file:
            self.dev_conf.capture_run.caps_remaining = 5
            
        self.ctrl_util.set_capture_run_length()
    
        # Checks run_setup completes successfully, calls it with captures if save_file is not true
        if (self.pico.run_setup() if save_file else self.pico.run_setup(captures)):
            start_acq_time = time.time()
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
                self.cap_times.append(time.time() - start_acq_time)
                start_fw_time = time.time()
                self.file_writer.write_hdf5()
                self.file_writer.file_times.append(time.time() - start_fw_time)

        self.dev_conf.capture_run.reset()

    def capture_run(self):
        """Run the necessary steps for a capture."""
        # Run the scope, and update the captures completed
        self.pico.assign_pico_memory()
        start_time = time.time()
        self.pico.run_block()
        self.trig_rate_hz = f"{round(self.pico.seg_caps / (time.time() - start_time), 2)}Hz"
        self.dev_conf.capture_run.caps_comp += self.pico.seg_caps * len(
            self.buffer_manager.active_channels
        )

        # Process the data, for the purposes of LV and PHA
        if not self.pico_status.flags.abort_cap:
            self.buffer_manager.save_lv_data(False)
            self.analysis.pha_one_peak()

    def tb_capture(self):
        """
        """
        # validate this method of calculating max captures!
        self.ctrl_util.set_capture_run_limits()
        self.dev_conf.capture_run.caps_in_run = int(self.dev_conf.capture_run.caps_max/2)
        start_tb_time = time.time()
        self.pico.run_time_based_capture(
            self.dev_conf.capture.capture_time
            )
        self.cap_times.append(time.time() - start_tb_time)
        self.file_writer.write_hdf5(write_accumulated=True)
        self.buffer_manager.save_lv_data(True)
        self.buffer_manager.clear_arrays()
        self.pico_status.flags.abort_cap = False
   
    def set_temp_single_shot(self, _=None):
        """
        Called when the user sets /gpib/set/set_temp.
        Reads temp_target and starts a background waiting thread.
        """
        T = self.gpib_config.temp_target
        self.pico_status.flags.temp_set     = True
        self.pico_status.flags.temp_reached = False
        self.pico_status.flags.system_state = f"Setting TEC {T:.2f} °C"
        self._bg_set_and_wait(T)

    def set_listening(self, value):
        self.gpio_config.listening = value
        if value:
            if self.file_writer.check_file_name():
                self.file_writer.file_error = False
                self.pico_status.flags.system_state = "Listening for triggers"
                self.gpio_config.missed_triggers = 0
                self.gpio_config.unexpected_triggers = 0
                self.cap_times = []
                self.file_writer.file_times = []
            else:
                self.file_writer.file_error = True
                self.pico_status.flags.system_state = (
                    "File Name Empty or Already Exists")
                self.pico_status.flags.user_capture = False
                self.gpio_config.listening = False
        else:
            self.gpio_config.gpio_captures = 0


    @run_on_executor
    def _bg_set_and_wait(self, T: float):
        """
        Background thread to write the setpoint and wait_for_tec until stable
        """
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
        self.gpib_util.wait_for_tec(T, self.gpib_config.tol)

        self.pico_status.flags.temp_set     = False
        self.pico_status.flags.temp_reached = True

        
    ##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        """Execute thread, responsible for calling the run_capture function at timed intervals."""
        while self.update_loop_active:
            if not self.gpio_config.listening:
                self.run_capture()
                time.sleep(0.2)
            elif self.gpio_config.capture:
                self.run_capture()
                time.sleep(0.05)
            else:
                time.sleep(0.05)

    def set_update_loop_state(self, state=bool):
        """Set the state of the update_loop in the executor thread."""
        self.update_loop_active = state

    def cleanup(self):
        """Responsible for ensuring the picoscope is closed cleanly when the adapter is shutdown."""
        self.set_update_loop_state(False)
        self.pico_status.flags.abort_cap = True
        self.gpio_config.listening = False
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

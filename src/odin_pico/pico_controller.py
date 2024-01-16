import math
import time
import logging

from functools import partial
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.concurrent import run_on_executor
from concurrent import futures

from odin_pico.pico_util import PicoUtil
from odin_pico.pico_device import PicoDevice
from odin_pico.buffer_manager import BufferManager
from odin_pico.file_writer import FileWriter
from odin_pico.analysis import PicoAnalysis

from odin_pico.DataClasses.device_config import DeviceConfig
from odin_pico.DataClasses.device_status import DeviceStatus

class PicoController():
    executor = futures.ThreadPoolExecutor(max_workers=2)

    def __init__(self, lock, loop, path):
        # Threading lock and control variables
        self.lock = lock
        self.update_loop_active = loop
        self.lv_captures = 1

        self.enable = False

        # Objects for handling configuration, data storage and representing the PicoScope 5444D
        self.dev_conf = DeviceConfig()
        self.dev_conf.file.file_path = path
        self.channels = [self.dev_conf.channel_a, self.dev_conf.channel_b, self.dev_conf.channel_c, self.dev_conf.channel_d]
        self.util = PicoUtil()
        self.pico_status = DeviceStatus()
        self.buffer_manager = BufferManager(self.dev_conf)
        self.file_writer = FileWriter(self.dev_conf, self.buffer_manager, self.pico_status) 
        self.analysis = PicoAnalysis(self.dev_conf, self.buffer_manager, self.pico_status)
        self.pico = PicoDevice(self.dev_conf, self.pico_status, self.buffer_manager)
        
        # ParameterTree's to represent different parts of the system
        adapter_status = ParameterTree({
            'settings_verified': (lambda: self.pico_status.flags.verify_all, None),
            'open_unit': (lambda: self.pico_status.open_unit, None),
            'pico_setup_verify': (lambda: self.pico_status.pico_setup_verify, None),
            'channel_setup_verify': (lambda: self.pico_status.channel_setup_verify, None),
            'channel_trigger_verify': (lambda: self.pico_status.channel_trigger_verify, None),
            'capture_settings_verify': (lambda: self.pico_status.capture_settings_verify, None)
        })
  
        self.chan_params = {}
        for name in self.dev_conf.channel_names:
            self.chan_params[name] = ParameterTree({
                'channel_id': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'channel_id'), None),
                'active': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'active'), partial(self.set_dc_chan_value, self.dev_conf, f'channel_{name}', 'active')),
                'verified': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'verified'), None),
                'live_view': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'live_view'), partial(self.set_dc_chan_value, self.dev_conf, f'channel_{name}', 'live_view')),
                'coupling': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'coupling'), partial(self.set_dc_chan_value, self.dev_conf, f'channel_{name}', 'coupling')),
                'range': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'range'), partial(self.set_dc_chan_value, self.dev_conf, f'channel_{name}', 'range')),
                'offset': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'offset'), partial(self.set_dc_chan_value, self.dev_conf, f'channel_{name}', 'offset')),
                'pha_active': (partial(self.get_dc_value, self.dev_conf, f'channel_{name}', 'pha_active'), partial(self.set_dc_chan_value, self.dev_conf, f'channel_{name}', 'pha_active'))
                })

        pico_trigger = ParameterTree({
            'active': (lambda: self.dev_conf.trigger.active, partial(self.set_dc_value, self.dev_conf.trigger, "active")),
            'auto_trigger': (lambda: self.dev_conf.trigger.auto_trigger_ms, partial(self.set_dc_value, self.dev_conf.trigger, "auto_trigger_ms")),
            'direction': (lambda: self.dev_conf.trigger.direction, partial(self.set_dc_value, self.dev_conf.trigger, "direction")),
            'delay': (lambda: self.dev_conf.trigger.delay, partial(self.set_dc_value, self.dev_conf.trigger, "delay")),
            'source': (lambda: self.dev_conf.trigger.source, partial(self.set_dc_value, self.dev_conf.trigger, "source")),
            'threshold': (lambda: self.dev_conf.trigger.threshold, partial(self.set_dc_value, self.dev_conf.trigger, "threshold"))
        })

        pico_capture = ParameterTree({
            'pre_trig_samples': (lambda: self.dev_conf.capture.pre_trig_samples, partial(self.set_dc_value, self.dev_conf.capture, "pre_trig_samples")),
            'post_trig_samples': (lambda: self.dev_conf.capture.post_trig_samples, partial(self.set_dc_value, self.dev_conf.capture, "post_trig_samples")),
            'n_captures': (lambda: self.dev_conf.capture.n_captures, partial(self.set_dc_value, self.dev_conf.capture, "n_captures"))
        })

        pico_mode = ParameterTree({
            'resolution': (lambda: self.dev_conf.mode.resolution, partial(self.set_dc_value, self.dev_conf.mode, "resolution")),
            'timebase': (lambda: self.dev_conf.mode.timebase, partial(self.set_dc_value, self.dev_conf.mode, "timebase")),
            'samp_time': (lambda: self.dev_conf.mode.samp_time, None)
        })

        pico_file = ParameterTree({
            'folder_name': (lambda: self.dev_conf.file.folder_name, partial(self.set_dc_value, self.dev_conf.file, "folder_name")),
            'file_name': (lambda: self.dev_conf.file.file_name, partial(self.set_dc_value, self.dev_conf.file, "file_name")),
            'file_path': (lambda: self.dev_conf.file.file_path, None),
            'curr_file_name': (lambda: self.dev_conf.file.curr_file_name, None),
            'last_write_success': (lambda: self.dev_conf.file.last_write_success, None)
        })

        pico_pha = ParameterTree({
            'num_bins': (lambda: self.dev_conf.pha.num_bins, partial(self.set_dc_value, self.dev_conf.pha, "num_bins")),
            'lower_range': (lambda: self.dev_conf.pha.lower_range, partial(self.set_dc_value, self.dev_conf.pha, "lower_range")),
            'upper_range': (lambda: self.dev_conf.pha.upper_range, partial(self.set_dc_value, self.dev_conf.pha, "upper_range"))
        })

        pico_settings = ParameterTree({
            'mode': pico_mode,
            'channels': {name: channel for (name, channel) in self.chan_params.items()},
            'trigger': pico_trigger,
            'capture': pico_capture,
            'file': pico_file,
            'pha': pico_pha
        })

        live_view = ParameterTree({
            'lv_active_channels': (lambda: self.buffer_manager.lv_channels_active, None),
            'pha_counts': (lambda: self.buffer_manager.pha_counts, None),
            'capture_count': (lambda: self.dev_conf.capture_run.live_cap_comp, None),
            'captures_requested': (lambda: self.dev_conf.capture.n_captures, None),
            'lv_data': (lambda: self.buffer_manager.lv_channel_arrays, None),
            'pha_bin_edges': (lambda: self.buffer_manager.bin_edges, None),
            'lv_range': (lambda: self.buffer_manager.lv_range, partial(self.set_dc_value, self.buffer_manager, "lv_range")),
            'pha_active_channels': (lambda: self.buffer_manager.pha_active_channels, None),
        })

        pico_commands = ParameterTree({
            'run_user_capture': (lambda: self.pico_status.flags.user_capture, partial(self.set_dc_value, self.pico_status.flags, "user_capture")),
            'clear_pha': (lambda: self.buffer_manager.clear_pha, partial(self.set_dc_value, self.buffer_manager, "clear_pha"))
        })

        pico_flags = ParameterTree({
            'abort_cap': (lambda: self.pico_status.flags.abort_cap, partial(self.set_dc_value, self.pico_status.flags, "abort_cap")),
            'system_state': (lambda: self.pico_status.flags.system_state, None)
        })

        self.pico_param_tree = ParameterTree({
            'status': adapter_status,
            'commands': pico_commands,
            'settings': pico_settings,
            'flags': pico_flags,
            'live_view': live_view
        })

        self.param_tree = ParameterTree({
            'device': self.pico_param_tree
        })

        # Initalise the "update_loop" if control variable passed to the Pico_Controller is True
        if self.update_loop_active:
            self.update_loop()

        # Set initial state of the verification system
        self.verify_settings()
        # print(f'using get_dc_value: {self.get_dc_value(self.dev_conf, f"channel_B", "channel_id")}')

    def get_dc_value(self, obj, chan_name, attr_name):
        try:
            channel_dc = getattr(obj, chan_name)
            return getattr(channel_dc, attr_name, None)
        except AttributeError:
            return None

    def set_dc_value(self, obj, attr_name, value):
 
        if (attr_name == "num_bins") or (attr_name == "lower_range") or (attr_name == "upper_range"):
            self.buffer_manager.clear_pha = True

        if (attr_name == 'clear_pha'):
            for chan in range(4):
                self.set_dc_chan_value(self.dev_conf, f'channel_{chr(chan+97)}', 'pha_active', False)

        setattr(obj, attr_name, value)
    
    def set_dc_chan_value(self, obj, chan_name, attr_name, value):

        if (attr_name == 'live_view'):
            try:
                channel_dc = getattr(obj, chan_name)
                if getattr(channel_dc, 'active', None) == True:
                    setattr(channel_dc, attr_name, value)
            except AttributeError:
                pass

        elif (attr_name == 'active') and (value == False):
            try:
                channel_dc = getattr(obj, chan_name)
                setattr(channel_dc, 'live_view', value)
                setattr(channel_dc, attr_name, value)
            except AttributeError:
                pass
        else:
            try:
                channel_dc = getattr(obj, chan_name)
                setattr(channel_dc, attr_name, value)
            except AttributeError:
                pass

    def verify_settings(self):
        """
            Verifies all picoscope settings, sets status of individual groups of settings
        """

        active = [self.dev_conf.channel_a.active, self.dev_conf.channel_b.active, self.dev_conf.channel_c.active, self.dev_conf.channel_d.active]

        self.pico_status.pico_setup_verify = self.util.verify_mode_settings(active,self.dev_conf.mode)
        for chan in self.channels:
            chan.verified = self.util.verify_channel_settings(chan.offset)
        self.pico_status.channel_setup_verify = self.util.set_channel_verify_flag(self.channels)
        self.pico_status.channel_trigger_verify = self.util.verify_trigger(self.channels, self.dev_conf.trigger)
        self.pico_status.capture_settings_verify = self.util.verify_capture(self.dev_conf.capture)
        self.pico_status.flags.verify_all = self.set_verify_flag()

    def set_verify_flag(self):
        """
            Used by the verify_settings() function to return the Boolean value of the setting verified flag
        """

        status_list = [self.pico_status.pico_setup_verify, self.pico_status.channel_setup_verify, self.pico_status.channel_trigger_verify, self.pico_status.capture_settings_verify]
        for status in status_list:
            if status != 0:
                return False
        return True
    
    def set_capture_run_limits(self):
        """
            Set the value for maximum amount of captures that can fit into the picoscope memory taking 
            into accountcurrent user settings as well as setting the captures_remaning variable
        """

        capture_samples = self.dev_conf.capture.pre_trig_samples + self.dev_conf.capture.post_trig_samples
        self.dev_conf.capture_run.caps_max = math.floor(self.util.max_samples(self.dev_conf.mode.resolution) / capture_samples)
        self.dev_conf.capture_run.caps_remaining = self.dev_conf.capture.n_captures

    def set_capture_run_length(self):
        """
            Sets the captures to be completed in each "run" based on the maximum allowed captures, and
            the amount of captures left to be collected
        """
        if len(self.buffer_manager.active_channels) > 0:
            max_caps = math.trunc((self.dev_conf.capture_run.caps_max)/(len(self.buffer_manager.active_channels)))
        else
            max_caps = self.dev_conf.capture_run.caps_max

        # print("SET CAPTURE RUN LENGTH ACTIVE CHANNELS", self.buffer_manager.active_channels)

        if self.dev_conf.capture_run.caps_remaining <= max_caps:
            self.dev_conf.capture_run.caps_in_run = self.dev_conf.capture_run.caps_remaining
        else:
            self.dev_conf.capture_run.caps_in_run = max_caps

    def calc_samp_time(self):
        """
            Calculates the sample interval based on the resolution and timebase
        """

        if self.dev_conf.mode.resolution == 0:
            if ((self.dev_conf.mode.timebase) >= 0 and (self.dev_conf.mode.timebase <= 2)):
                self.dev_conf.mode.samp_time = (math.pow(2, self.dev_conf.mode.timebase) / (1000000000))
            else:
                self.dev_conf.mode.samp_time = ((self.dev_conf.mode.timebase - 2) / (125000000))
        elif self.dev_conf.mode.resolution == 1:
            if ((self.dev_conf.mode.timebase) >= 1 and (self.dev_conf.mode.timebase <= 3)):
                self.dev_conf.mode.samp_time = (math.pow(2, self.dev_conf.mode.timebase - 1) / (500000000))
            else:
                self.dev_conf.mode.samp_time = ((self.dev_conf.mode.timebase - 3) / (62500000))

    def run_capture(self):
        """
            Responsible for telling the picoscope to collect and return data
        """

        self.calc_samp_time()
        if self.pico_status.flags.verify_all:
            self.check_res()
            self.start_capture(self.pico_status.flags.user_capture)

        if ((self.pico_status.open_unit == 0) and (self.pico_status.flags.verify_all is False)):
            self.pico_status.flags.system_state = "Connected to PicoScope, Idle"       

    def check_res(self):
        """
            Detect if the device resolution has been changed, if so apply to picoscope
        """

        if self.pico_status.flags.res_changed:
            if self.pico_status.open_unit == 0:
                self.pico.stop_scope()
            self.pico_status.flags.res_changed = False

    def start_capture(self, save_file):
        """
            Run the appropriate steps for a capture, which changes depending on whether it will be 
            saved to a file
        """

        captures = self.dev_conf.capture.n_captures
        self.set_capture_run_limits()
        if self.pico.run_setup():
            while self.dev_conf.capture_run.caps_comp < captures:
                start_time = time.time()
                self.set_capture_run_length()
                self.pico.assign_pico_memory()
                self.pico.run_block()
                self.dev_conf.capture_run.caps_comp += self.dev_conf.capture_run.caps_in_run
                self.dev_conf.capture_run.caps_remaining -= self.dev_conf.capture_run.caps_in_run
                chan = 0
                for array in self.buffer_manager.np_channel_arrays:
                    print("CHANNEL", chan, "PREVIEW")
                    chan += 1
                    if len(array) > 1200:
                        print(array[1160])
                    else:
                        print(array[2])

            self.analysis.PHA_one_peak(save_file)
            self.buffer_manager.save_lv_data()
            print(len(self.buffer_manager.np_channel_arrays))

            for a in range(len(self.buffer_manager.np_channel_arrays)):
            # if len(self.buffer_manager.np_channel_arrays) > 1:
                temp = self.buffer_manager.np_channel_arrays[a]


                # temp = self.buffer_manager.np_channel_arrays[0]
                # print("LENGTH OF ARRAY", len(temp))
                for i in range(3):
                    print("Number", i, temp[i])
                for x in range((len(temp)-3), len(temp)):
                    print("Number", x, temp[x])

                for value in range((len(temp))-4):
                    if temp[value][0] == 0:
                        if temp[value + 1][0] == 0:
                            if temp [value + 2][0] == 0:
                                if temp[value + 3][0] != 0:
                                    print("CHANNEL", a)
                                    print("VALUE =", value)
                                    print("A =", temp[value])
                                    print("A + 1 =", temp[value+1])
                                    print("A + 2 =", temp[value+2])
                                    print("A + 3 =", temp[value + 3])



            if save_file == True:
                self.file_writer.writeHDF5()

        self.dev_conf.capture_run.reset()
        
        if save_file == True:
            self.pico_status.flags.user_capture = False


##### Adapter specific functions below #####

    @run_on_executor
    def update_loop(self):
        """Function that is called in an executor thread, responsible for calling the run_capture function at timed intervals """
        
        while self.update_loop_active:
            self.run_capture()
            time.sleep(0.2)

    def set_update_loop_state(self, state=bool):
        """Sets the state of the update_loop in the executor thread"""

        self.update_loop_active = state

    def cleanup(self):
        """Responsible for making sure the picoscope is closed cleanly when the adapter is shutdown"""

        self.set_update_loop_state(False)
        self.pico.stop_scope()
        logging.debug("Stopping PicoScope services and closing device")

    def get(self, path):
        """Get the parameter tree. """

        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree. """

        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise PicoControllerError(e)
        self.verify_settings()      
 
class PicoControllerError(Exception):
    pass
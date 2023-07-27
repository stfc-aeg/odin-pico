import ctypes
from datetime import datetime
import logging
import time
import numpy as np
import h5py

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

from odin_pico.pico_config import DeviceConfig
from odin_pico.pico_status import Status
from odin_pico.buffer_manager import BufferManager
from odin_pico.pico_util import PicoUtil
from odin_pico.PS5000A_Trigger_Info import Trigger_Info

class PicoDevice():
    def __init__(self, dev_conf=DeviceConfig(None), pico_status=Status(), buffer_manager=BufferManager()):

        # def __init__(self, dev_conf=None,pico_status=None,buffer_manager=None):
        #   self.dev_conf = dev_conf if dev_conf is not None else DeviceConfig()
        self.util = PicoUtil()
        self.dev_conf = dev_conf
        self.pico_status = pico_status
        self.buffer_manager = buffer_manager
        self.cap_time = 30
        self.caps = 0

    def open_unit(self):
        """
            Responsible for initalising connection with the picoscope, and settings the status values.
        """

        logging.debug(f'Trying to open Device')
        self.pico_status.status["open_unit"] = ps.ps5000aOpenUnit(ctypes.byref(self.dev_conf.mode["handle"]), None, self.dev_conf.mode["resolution"])
        if self.pico_status.status["open_unit"] == 0:
            self.pico_status.status["maximumValue"] = ps.ps5000aMaximumValue(self.dev_conf.mode["handle"], ctypes.byref(self.dev_conf.meta_data["max_adc"]))
        logging.debug(f'open_unit value:{self.pico_status.status["open_unit"]} /nopen_unit() finished')

    def generate_arrays(self, *args):
        """
            Responsible for generating local arrays in the buffer_manager for the picoscope to write to.
            Takes *arg to set array limit to 1 for a single liveview capture
        """
        if args:
            n_captures = args[0]
            self.buffer_manager.generate_arrays(n_captures)
        else:
            n_captures = self.dev_conf.capture["n_captures"]
            self.buffer_manager.generate_arrays()

    def assign_pico_memory(self, *args):
        """
            Responsible for mapping the local buffers in the buffer_manager to the picoscope for
            each individual trace to be captured on each channel by the picoscope  
        """
        if True:#self.ping_scope():
            if args:
                n_captures = args[0]
            else:
                pass
            n_captures = self.dev_conf.capture_run["caps_in_run"]
            self.pico_status.status["memory_segments"] = ps.ps5000aMemorySegments(self.dev_conf.mode["handle"], n_captures,
                                                                                ctypes.byref(self.dev_conf.meta_data["samples_per_seg"]))
            self.pico_status.status["set_no_captures"] = ps.ps5000aSetNoOfCaptures(self.dev_conf.mode["handle"], n_captures)
            samples=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])

            for c,b in zip(self.buffer_manager.active_channels, self.buffer_manager.channel_arrays):
                for i in range(self.dev_conf.capture_run["caps_comp"],self.dev_conf.capture_run["caps_comp"]+self.dev_conf.capture_run["caps_in_run"]):
                    buff = b[i]
                    self.pico_status.status[f'SetDataBuffer'] =  ps.ps5000aSetDataBuffer(self.dev_conf.mode["handle"], c, buff.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), 
                                                                                                samples, i-self.dev_conf.capture_run["caps_comp"], 0)

    def set_trigger(self):
        """
            Responsible for setting the trigger information on the picoscope
        """
        if True:#self.ping_scope():
            threshold = int(mV2adc(self.dev_conf.trigger["threshold"], (self.dev_conf.channels[self.util.channel_names_dict[self.dev_conf.trigger["source"]]]["range"])
                                ,self.dev_conf.meta_data["max_adc"]))
            self.pico_status.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.dev_conf.mode["handle"], self.dev_conf.trigger["active"], self.dev_conf.trigger["source"], threshold, 
                                                                            self.dev_conf.trigger["direction"], self.dev_conf.trigger["delay"], self.dev_conf.trigger["auto_trigger_ms"])
        
    def set_channels(self):
        
        """
            Responsible for setting the channel information for each channel on the picoscope
        """
        if True:#self.ping_scope():
            for chan in self.dev_conf.channels:

                max_v = ctypes.c_float(0)
                min_v = ctypes.c_float(0)

                ps.ps5000aGetAnalogueOffset(self.dev_conf.mode["handle"],self.dev_conf.channels[chan]["range"], self.dev_conf.channels[chan]["coupling"], ctypes.byref(max_v), ctypes.byref(min_v))
                logging.debug(f'Max offset:{max_v.value} Min offset:{min_v.value}')


                offset = self.util.calc_offset(self.dev_conf.channels[chan]["range"],self.dev_conf.channels[chan]["offset"])

                logging.debug(f'calculated offset value: {offset} based on percentage of {self.dev_conf.channels[chan]["offset"]}')
                self.pico_status.status["set_channels"] = ps.ps5000aSetChannel(self.dev_conf.mode["handle"], self.dev_conf.channels[chan]["channel_id"], int(self.dev_conf.channels[chan]["active"]), 
                                                            self.dev_conf.channels[chan]["coupling"], self.dev_conf.channels[chan]["range"], offset)
    
    def run_setup(self, *args):
        """
            Responsible for "setting up" the picoscope, calling functions that apply local settings to the picoscope
            and for calling the buffer generating function
        """
        if self.pico_status.status["open_unit"] != 0:
            self.pico_status.flag["system_state"] = "Waiting for connection"
            self.open_unit()
        if self.pico_status.status["open_unit"] == 0:
            self.pico_status.flag["system_state"] = "Connected to Picoscope, running setup"
            self.set_channels()
            self.set_trigger() 
            if args:
                self.buffer_manager.generate_arrays(args[0])
            else:
                self.buffer_manager.generate_arrays()
            return True

    def run_block(self):
        """
            Responsible for telling the picoscope how much data to collect and
            when to collect it, retrives that data into local buffers once
            data collection is finished
        """
        self.caps = 0
        #print(f'\n\npico_status when called: {self.pico_status.status}')
        if True:#self.ping_scope():
            start_time = time.time()
            self.pico_status.status["block_ready"] = ctypes.c_int16(0)
            self.dev_conf.meta_data["total_cap_samples"]=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])
            self.dev_conf.meta_data["max_samples"] = ctypes.c_int32(self.dev_conf.meta_data["total_cap_samples"])
            self.pico_status.status["run_block"] =  ps.ps5000aRunBlock(self.dev_conf.mode["handle"], self.dev_conf.capture["pre_trig_samples"], 
                                                                        self.dev_conf.capture["post_trig_samples"], self.dev_conf.mode["timebase"], None, 0, None, None)
            self.pico_status.flag["system_state"] = "Connected to Picoscope, starting data collection"
            while self.pico_status.status["block_ready"].value == self.pico_status.status["block_check"].value:
                self.pico_status.status["is_ready"] =  ps.ps5000aIsReady(self.dev_conf.mode["handle"], ctypes.byref(self.pico_status.status["block_ready"]))
                if (time.time() - start_time >= 0.25):
                    start_time = time.time()
                    self.ping_cap_count()
                    print(f'Caps: {self.dev_conf.capture_run["live_cap_comp"]}')
                    pass
                if (self.pico_status.flag["abort_cap"]):
                    ps.ps5000aStop(self.dev_conf.mode["handle"])
                    print(f'Aborting capture')
           #print(f'\n\npico_status before get_values: {self.pico_status.status}')
            self.ping_cap_count()
            self.pico_status.flag["system_state"] = "Connected to Picoscope, returning data to pc"
           
            logging.debug(f'getting values from {self.dev_conf.capture_run["caps_comp"]} to {(self.dev_conf.capture_run["caps_comp"]+self.dev_conf.capture_run["caps_in_run"]-1)}')
            
            self.pico_status.status["get_values"] = ps.ps5000aGetValuesBulk(self.dev_conf.mode["handle"], ctypes.byref(self.dev_conf.meta_data["max_samples"]), 0, 
                                                                (self.dev_conf.capture_run["caps_in_run"]-1), 0, 0, ctypes.byref(self.buffer_manager.overflow))
            self.pico_status.flag["system_state"] = "Connected to Picoscope, calculating trigger timings"
            self.get_trigger_timing()
            

    def get_trigger_timing(self):
        trigger_info = (Trigger_Info*self.dev_conf.capture_run["caps_in_run"]) ()
        ps.ps5000aGetTriggerInfoBulk(self.dev_conf.mode["handle"], ctypes.byref(trigger_info), 0, (self.dev_conf.capture_run["caps_in_run"]-1))

        last_samples = 0
        for i in trigger_info:
            sample_interval = i.timeStampCounter - last_samples
            time_interval = sample_interval * self.dev_conf.mode["samp_time"]
            last_samples = i.timeStampCounter
            self.buffer_manager.trigger_times.append(time_interval)

      
    def ping_scope(self):
        """
            Responsible for checking the connection to the picoscope is still live
        """
        if (ps.ps5000aPingUnit(self.dev_conf.mode["handle"])) == 0:
            return True
        else:
            self.pico_status.status["open_unit"] = -1
            return False
        
    def ping_cap_count(self):
        """
            Responsible for querying the picoscope to check how many traces have 
            been captured
        """
        caps = ctypes.c_uint32(0)
        ps.ps5000aGetNoOfCaptures(self.dev_conf.mode["handle"], ctypes.byref(caps))
        self.dev_conf.capture_run["live_cap_comp"] = (self.dev_conf.capture_run["caps_comp"] + caps.value)
    
    def stop_scope(self):
        """
            Responsible for telling the picoscope to stop its current activity
            and to close the connection 
        """
        if True:#self.ping_scope():
            self.pico_status.status["stop"] = ps.ps5000aStop(self.dev_conf.mode["handle"])
            self.pico_status.status["close"] = ps.ps5000aCloseUnit(self.dev_conf.mode["handle"])
            if self.pico_status.status["stop"] == 0:
                self.pico_status.status["open_unit"] = -1
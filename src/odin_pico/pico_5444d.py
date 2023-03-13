import ctypes
import time
import numpy as np
import h5py

import logging
from functools import partial

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from concurrent.futures import thread
from tornado.concurrent import run_on_executor
from concurrent import futures

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

from odin_pico.pico_connect_functions import PicoFunctions

class P5444D():
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self,lock):
        self.handle = ctypes.c_int16(0)
        self.pico = PicoFunctions(np.int16(self.handle))
        self.lock = lock

        self.resolution = None
        self.timebase = 0
        self.connection_attempted = -1

        self.channel_names = ['a', 'b', 'c', 'd']

        self.channels = {}
        for name in self.channel_names:
            self.channels[name] = {
                "name": name,
                "active": False,
                "verified": False,
                "coupling": "PS5000A_DC",
                "range": "PS5000A_10MV", 
                "offset": 0.0
            }

        self.capture = {
            "pre_trig_samples": 0,
            "post_trig_samples": 0,
            "n_captures": 0
        }

        self.trigger = {
            "active": False,
            "source": "PS5000A_CHANNEL_A",
            "threshold": 50,
            "direction": "PS5000A_RISING",
            "delay": 0,
            "auto_trigger_ms": 0
        }

        # status codes for the different components of the picoscope setup
        self.status = {
            "openunit": -1,
            "pico_setup_verify": -1,
            "pico_setup_complete": -1,
            "channel_setup_verify": -1,
            "channel_setup_complete": -1,
            "channel_trigger_verify": -1,
            "channel_trigger_complete": -1,
            "capture_settings_verify": -1,
            "capture_settings_complete": -1,
            "stop": -1,
            "close": -1
        }

        adapter_status = ParameterTree ({
            'openunit': (lambda: self.status["openunit"], None),
            'pico_setup_verify': (lambda: self.status["pico_setup_verify"], None),
            'pico_setup_complete': (lambda: self.status["pico_setup_complete"], self.complete_channels_defined),
            'channel_setup_verify': (lambda: self.status["channel_setup_verify"], None),
            'channel_setup_complete': (lambda: self.status["channel_setup_complete"], self.complete_channel_settings),
            'channel_trigger_verify': (lambda: self.status["channel_trigger_verify"], None),
            'channel_trigger_complete': (lambda: self.status["channel_trigger_complete"], self.complete_trigger_settings),
            'capture_settings_verify': (lambda: self.status["capture_settings_verify"], None),
            'capture_settings_complete': (lambda: self.status["capture_settings_complete"], self.complete_capture_settings)
        })

        pico_connection = ParameterTree ({
            'resolution': (lambda: self.resolution, self.set_resolution),
            'connect': (lambda: self.connection_attempted, self.commit_resolution)
        })

        self.chan_params = {}
        for channel in self.channel_names:
            self.chan_params[channel] = ParameterTree(
                {
                'active': (partial(self.get_channel_active, channel), partial(self.set_channel_active, channel)),
                'verified': (partial(self.get_channel_verified, channel), None),
                'coupling': (partial(self.get_channel_coupling, channel), partial(self.set_channel_coupling, channel)),
                'range': (partial(self.get_channel_range, channel), partial(self.set_channel_range, channel)),
                'offset': (partial(self.get_channel_offset, channel), partial(self.set_channel_offset, channel))
                }
            )

        pico_trigger = ParameterTree ({
            'active': (lambda: self.trigger["active"], self.set_trigger_active),
            'auto_trigger': (lambda: self.trigger["auto_trigger_ms"], self.set_trigger_auto),
            'direction': (lambda: self.trigger["direction"],self.set_trigger_direction),
            'delay': (lambda: self.trigger["delay"], self.set_trigger_delay),
            'source': (lambda: self.trigger["source"], self.set_trigger_source),
            'threshold': (lambda: self.trigger["threshold"], self.set_trigger_threshold)
        })

        pico_capture = ParameterTree ({
            'pre_trig_samples': (lambda: self.capture["pre_trig_samples"], self.set_pre_trig_samples),
            'post_trig_samples': (lambda: self.capture["post_trig_samples"], self.set_post_trig_samples),
            'n_captures': (lambda: self.capture["n_captures"], self.set_n_captures)
        })

        pico_settings = ParameterTree ({
            'timebase': (lambda: self.timebase, self.set_timebase),
            'channels':{name: channel for (name, channel) in self.chan_params.items()},
            'trigger': pico_trigger,
            'capture': pico_capture
        })

        self.pico_param_tree = ParameterTree ({
            'status': adapter_status,
            'connection': pico_connection,
            'settings': pico_settings
        })

    # Return functions for channel parameters to avoid late binding issues
    def get_channel_active(self, channel):
        return self.channels[channel]["active"]
    
    def get_channel_verified(self, channel):
        return self.channels[channel]["verified"]
        
    def get_channel_coupling(self, channel):
        return self.channels[channel]["coupling"]

    def get_channel_range(self, channel):
        return self.channels[channel]["range"]

    def get_channel_offset(self, channel):
        return self.channels[channel]["offset"]

    # Setter functions for all ParameterTree attributes 
    def set_pre_trig_samples(self, samples):
        self.capture["pre_trig_samples"] = samples
        self.verify_capture(1)
    
    def set_post_trig_samples(self, samples):
        self.capture["post_trig_samples"] = samples
        self.verify_capture(1)

    def set_n_captures(self, samples):
        self.capture["n_captures"] = samples
        self.verify_capture(1)

    def set_trigger_active(self, active):
        self.trigger["active"] = active
        self.verify_trigger(1)

    def set_trigger_auto(self, auto):
        self.trigger["auto_trigger_ms"] = auto
        self.verify_trigger(1)

    def set_trigger_direction(self, direction):
        self.trigger["direction"] = direction
        self.verify_trigger(1)

    def set_trigger_delay(self, delay):
        self.trigger["delay"] = delay
        self.verify_trigger(1)
    
    def set_trigger_source(self, source):
        self.trigger["source"] = source
        self.verify_trigger(1)

    def set_trigger_threshold(self, threshold):
        self.trigger["threshold"] = threshold
        self.verify_trigger(1)

    def set_resolution(self, resolution):
        self.resolution = resolution

    def set_timebase(self, timebase):
        self.timebase = timebase
        self.verify_channels_defined(1)

    def set_channel_active(self, channel, active):
        self.channels[channel]["active"] = active
        self.verify_channels_defined(1)

    def set_channel_coupling(self, channel, coupling):
        self.channels[channel]["coupling"] = coupling
        self.verify_channel_settings(channel)

    def set_channel_range(self, channel, range):
        self.channels[channel]["range"] = range
        self.verify_channel_settings(channel)

    def set_channel_offset(self, channel, offset):
        self.channels[channel]["offset"] = offset
        self.verify_channel_settings(channel)
    
    # Validation functions for various settings
    def verify_channels_defined(self, ver_atp):
        self.verify_attempted = 1
        channel_count = 0

        for channel in self.channels:
            if self.channels[channel]["active"] == True:
                channel_count += 1

        timebase = self.timebase
        if self.resolution == "PS5000A_DR_12BIT":
            if (timebase < 1):
                self.status["pico_setup_verify"] = -1
            elif (timebase == 1 and channel_count >0 and channel_count <2):
                self.status["pico_setup_verify"] = 0
            elif (timebase == 2 and channel_count >0 and channel_count <3):
                self.status["pico_setup_verify"] = 0
            elif (timebase >= 3 and channel_count >0 and channel_count <=4):
                self.status["pico_setup_verify"] = 0
            else:
                self.status["pico_setup_verify"] = -1

        if self.resolution == "PS5000A_DR_8BIT":
            if (timebase < 0):
                self.status["pico_setup_verify"] = -1
            elif (timebase == 0 and channel_count >0 and channel_count <2):
                self.status["pico_setup_verify"] = 0 
            elif (timebase == 1 and channel_count >0 and channel_count <3):
                self.status["pico_setup_verify"] = 0
            elif (timebase >= 2 and channel_count >0 and channel_count <=4):
                self.status["pico_setup_verify"] = 0
            else:
                self.status["pico_setup_verify"] = -1
        
        if channel_count == 0:
            self.status["pico_setup_verify"] = -1   

    def complete_channels_defined(self, com_atp):
        error_count = 0
        for channel in self.channels:
            if (self.channels[channel]["active"] == True) and (self.status["pico_setup_verify"] == -1):
                error_count += 1
        if error_count == 0:
            self.status["pico_setup_complete"] = 0
        else:
            self.status["pico_setup_complete"] = -1


    def verify_channel_settings(self, channel):
        pico_range = ps.PS5000A_RANGE[self.channels[channel]["range"]]
        pico_coupling = ps.PS5000A_COUPLING[self.channels[channel]["coupling"]]
        offset = self.channels[channel]["offset"]

        max = ctypes.c_float()
        min = ctypes.c_float()

        try:
            ps.ps5000aGetAnalogueOffset(self.handle,pico_range,pico_coupling,ctypes.byref(max),ctypes.byref(min))
        except:
            pass

        if (offset >= np.float32(min) and offset <=np.float32(max)):
            self.channels[channel]["verified"] = True
        else:
            self.channels[channel]["verified"] = False

        error_count = 0
        for channel in self.channels:
            if (self.channels[channel]["active"] == True) and (self.channels[channel]["verified"] == False):
                error_count += 1
        if error_count == 0:
            self.status["channel_setup_verify"] = 0
        else:
            self.status["channel_setup_verify"] = -1
    
    def complete_channel_settings(self, com_atp):
        error_count = 0
        for channel in self.channels:
            if (self.channels[channel]["active"] == True) and (self.channels[channel]["verified"] == False):
                error_count += 1
        if error_count == 0:
            self.status["channel_setup_complete"] = 0
            self.verify_trigger(1) # To set inital state of verify when it is active in WEB UI
        else:
            self.status["channel_setup_complete"] = -1

    
    def verify_trigger(self, ver_atp):
        ps_channels = {"PS5000A_CHANNEL_A":'a',"PS5000A_CHANNEL_B":'b',"PS5000A_CHANNEL_C":'c',"PS5000A_CHANNEL_D":'d'}
        ps_ranges = {"PS5000A_10MV":10,"PS5000A_20MV":20,"PS5000A_50MV":50,"PS5000A_100MV":100,"PS5000A_200MV":200,"PS5000A_500MV":500,
                     "PS5000A_1V":1000,"PS5000A_2V":2000,"PS5000A_5V":5000,"PS5000A_10V":10000,"PS5000A_20V":20000}
        
        max_threshold = ps_ranges[self.channels[ps_channels[self.trigger["source"]]]["range"]]
        
        source_verify = False
        threshold_verify = False
        delay_verify = False
        auto_verify = False

        print("Before Delay")
        print(self.channels[ps_channels[self.trigger["source"]]]["active"])
        source_verify = (self.channels[ps_channels[self.trigger["source"]]]["active"])

        print("Before Threshold")
        print(self.trigger["threshold"] < max_threshold)
        threshold_verify = (self.trigger["threshold"] < max_threshold)

        print("Before Delay")
        print(self.trigger["delay"] >= 0 and self.trigger["delay"] <= 4294967295)
        delay_verify = (self.trigger["delay"] >= 0 and self.trigger["delay"] <= 4294967295)

        print("Before Trigger")
        print(self.trigger["auto_trigger_ms"] >= 0 and self.trigger["auto_trigger_ms"] <= 32767)
        auto_verify = (self.trigger["auto_trigger_ms"] >= 0 and self.trigger["auto_trigger_ms"] <= 32767)

        if (source_verify == True and threshold_verify == True and delay_verify == True and auto_verify == True):
            self.status["channel_trigger_verify"] = 0
            print("setting verify true")
        else:
            print("setting verify false")
            self.status["channel_trigger_verify"] = -1

    def complete_trigger_settings(self, ver_atp):
        if (self.status["channel_trigger_verify"] == 0):
            self.status["channel_trigger_complete"] = 0
        else:
            self.status["channel_trigger_complete"] = -1

    def verify_capture(self, ver_atp):
        verify = True

        print("Samples added: ",(self.capture["pre_trig_samples"] + self.capture["post_trig_samples"]))
        if ((self.capture["pre_trig_samples"] + self.capture["post_trig_samples"])) < 1:
            verify = False
            print("False")

        print("Number of captures: ",self.capture["n_captures"])
        if (self.capture["n_captures"]) < 1:
            verify = False
            print("False")

        print("Samples * captures: ",(self.capture["n_captures"]) * (self.capture["pre_trig_samples"] + self.capture["post_trig_samples"]))
        if ((self.capture["n_captures"]) * (self.capture["pre_trig_samples"] + self.capture["post_trig_samples"])) > 50000000:
            verify = False
            print("False")

        if verify == True:
            self.status["capture_settings_verify"] = 0
            print("Setting True")
        else:
            self.status["capture_settings_verify"] = -1
            print("Setting False")



    def complete_capture_settings(self, ver_atp):
        if (self.status["capture_settings_verify"] == 0):
            self.status["capture_settings_complete"] = 0
        else:
            self.status["capture_settings_complete"] = -1



    @run_on_executor
    def commit_resolution(self, con_atp):
        if self.status["openunit"] == -1:
            self.connection_attempted = con_atp
            res = ps.PS5000A_DEVICE_RESOLUTION[self.resolution]
            print("Attempting connection with res: ",res)
            self.status["openunit"] = self.pico.open_unit(res)

    def update_poll(self):
        pass

    def cleanup(self):
        logging.debug("Stoping picoscope services and closing device")
        self.stop_status = ps.ps5000aStop(self.handle)
        self.close_status = ps.ps5000aCloseUnit(self.handle)

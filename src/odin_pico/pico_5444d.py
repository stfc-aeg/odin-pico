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
from odin_pico.pico_dict import PsDictUtil 

class P5444D():
    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self,lock):
        self.handle = ctypes.c_int16(0)
        self.pico = PicoFunctions(np.int16(self.handle))
        self.dict_util = PsDictUtil()
        self.lock = lock

        self.resolution = 0
        self.timebase = 0
        self.connection_attempted = -1

        self.channel_names = ['a', 'b', 'c', 'd']
        self.channels = {}
        i = 0
        for name in self.channel_names:
            self.channels[name] = self.dict_util.set_channel_defaults(name,i)
            i += 1

        self.trigger = self.dict_util.set_trigger_defaults()
        self.capture = self.dict_util.set_capture_defaults()
        self.status = self.dict_util.set_status_defaults()

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
                'channel_id': (partial(self.get_channel_value, channel, "channel_id"), None),
                'active': (partial(self.get_channel_value, channel, "active"), partial(self.set_channel_value, channel, "active")),
                'verified': (partial(self.get_channel_value, channel,"verified"), None),
                'coupling': (partial(self.get_channel_value, channel, "coupling"), partial(self.set_channel_value, channel, "coupling")),
                'range': (partial(self.get_channel_value, channel, "range"), partial(self.set_channel_value, channel, "range")),
                'offset': (partial(self.get_channel_value, channel, "offset"), partial(self.set_channel_value, channel, "offset"))
                }
            )

        pico_trigger = ParameterTree ({
            'active': (lambda: self.trigger["active"], partial(self.set_trigger_value, "active")),
            'auto_trigger': (lambda: self.trigger["auto_trigger_ms"], partial(self.set_trigger_value, "auto_trigger_ms")),
            'direction': (lambda: self.trigger["direction"], partial(self.set_trigger_value, "direction")),
            'delay': (lambda: self.trigger["delay"], partial(self.set_trigger_value, "delay")),
            'source': (lambda: self.trigger["source"], partial(self.set_trigger_value, "source")),
            'threshold': (lambda: self.trigger["threshold"], partial(self.set_trigger_value, "threshold"))
        })

        pico_capture = ParameterTree ({
            'pre_trig_samples': (lambda: self.capture["pre_trig_samples"], partial(self.set_capture_value, "pre_trig_samples")),
            'post_trig_samples': (lambda: self.capture["post_trig_samples"], partial(self.set_capture_value, "post_trig_samples")),
            'n_captures': (lambda: self.capture["n_captures"], partial(self.set_capture_value, "n_captures"))
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

    # Return function for channel parameters to avoid late binding issues
    def get_channel_value(self,channel,value):
        return self.channels[channel][value]

    # Various generic setting funtions for values
    def set_resolution(self, resolution):
        print(type(resolution))
        self.resolution = resolution

    def set_timebase(self, timebase):
        self.timebase = timebase
        self.verify_channels_defined(1)

    def set_capture_value(self,key,value):
        self.capture[key] = value
        self.verify_capture(1)

    def set_trigger_value(self,key,value):
        if ((key != "source") and (key != "direction")):
            self.trigger[key] = value
            self.verify_trigger(1)
        if (key == "source"):
            if self.dict_util.ps_channels(value):
                self.trigger[key] = value
                self.verify_trigger(1)
        if (key == "direction"):
            if self.dict_util.ps_direction(value):
                self.trigger[key] = value
                self.verify_trigger(1)

    def set_channel_value(self, channel, key, value):
        if (key == "coupling"):
            if self.dict_util.ps_coupling(value):
                self.channels[channel][key] = value
                self.verify_channel_settings(channel)
        elif (key == "range"):
            if self.dict_util.ps_range(value):
                self.channels[channel][key] = value
                self.verify_channel_settings(channel)
        elif (key == "active"):
            self.channels[channel]["active"] = value
            self.verify_channels_defined(1)
        else:
            self.channels[channel][key] = value
            self.verify_channel_settings(channel)
    
    # Validation functions for various settings
    def verify_channels_defined(self, ver_atp):
        self.verify_attempted = 1
        channel_count = 0

        for channel in self.channels:
            if self.channels[channel]["active"] == True:
                channel_count += 1

        timebase = self.timebase
        if self.resolution == 1:
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

        if self.resolution == 0:
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
        ps_channels = {0:'a',1:'b',2:'c',3:'d'}
        ps_ranges = {"PS5000A_10MV":10,"PS5000A_20MV":20,"PS5000A_50MV":50,"PS5000A_100MV":100,"PS5000A_200MV":200,"PS5000A_500MV":500,
                     "PS5000A_1V":1000,"PS5000A_2V":2000,"PS5000A_5V":5000,"PS5000A_10V":10000,"PS5000A_20V":20000}
        
        max_threshold = ps_ranges[self.channels[ps_channels[self.trigger["source"]]]["range"]]
        #max_threshold = get_range_values_mv([self.channels[ps_channels[self.trigger["source"]]]["range"]])
        
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
        print("running capture command")
        self.run_capture()



    @run_on_executor
    def commit_resolution(self, con_atp):
        if self.status["openunit"] == -1:
            self.connection_attempted = con_atp
            #res = ps.PS5000A_DEVICE_RESOLUTION[self.resolution]
            print("Attempting connection with res: ",self.resolution)
            self.status["openunit"] = self.pico.open_unit(self.resolution)
    
    @run_on_executor
    def run_capture(self):
        # Set channels up
        for channel in self.channels:
            chan = self.channels[channel]
            self.pico.set_channel("channel_"+(str(chan["channel_id"])),chan["channel_id"],chan["active"],
                                  chan["coupling"],chan["range"],chan["offset"])
        
        # Set trigger 
        trig = self.trigger
        ps_channels = {0:'a',1:'b',2:'c',3:'d'}
        range = self.channels[ps_channels[self.trigger["source"]]]["range"]
        self.pico.set_simple_trigger(trig["source"],range,trig["threshold"])

        # Run Block command
        cap = self.capture
        self.pico.run_block(self.timebase,cap["pre_trig_samples"],cap["post_trig_samples"],cap["n_captures"])


    def update_poll(self):
        pass

    def cleanup(self):
        logging.debug("Stoping picoscope services and closing device")
        self.stop_status = ps.ps5000aStop(self.handle)
        self.close_status = ps.ps5000aCloseUnit(self.handle)

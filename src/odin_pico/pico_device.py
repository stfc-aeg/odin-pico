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

class PicoDevice():
    def __init__(self, dev_conf=DeviceConfig(), pico_status=Status(), buffer_manager=BufferManager()):
        self.util = PicoUtil()
        self.dev_conf = dev_conf
        self.pico_status = pico_status
        self.buffer_manager = buffer_manager

    def test_print(self):
        print(f'\ndev_conf ID within pico_device: {id(self.dev_conf)} Example attribute: {self.dev_conf.trigger["source"]} \n')

    def open_unit(self):
        self.pico_status.status["open_unit"] = ps.ps5000aOpenUnit(ctypes.byref(self.dev_conf.mode["handle"]), None, self.dev_conf.mode["resolution"])
        self.pico_status.status["maximumValue"] = ps.ps5000aMaximumValue(self.dev_conf.mode["handle"], ctypes.byref(self.dev_conf.meta_data["max_adc"]))

    def assign_buffers(self):
        self.buffer_manager.generate_arrays()
        self.pico_status.status["memory_segments"] = ps.ps5000aMemorySegments(self.dev_conf.mode["handle"], self.dev_conf.capture["n_captures"],
                                                                              ctypes.byref(self.dev_conf.meta_data["samples_per_seg"]))
        self.pico_status.status["set_no_captures"] = ps.ps5000aSetNoOfCaptures(self.dev_conf.mode["handle"], self.dev_conf.capture["n_captures"])
        samples=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])
        for c,b in zip(self.buffer_manager.active_channels,self.buffer_manager.channel_arrays):
            for i in range(len(b)):
                buff = b[i]
                self.pico_status.status[f'SetDataBuffer_{c}_{i}'] =  ps.ps5000aSetDataBuffer(self.dev_conf.mode["handle"], c, buff.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), samples, i, 0)
    
    def set_trigger(self):
        print(self.pico_status.status)
        threshold = int(mV2adc(self.dev_conf.trigger["threshold"], (self.dev_conf.channels[self.util.channel_names_dict[self.dev_conf.trigger["source"]]]["range"])
                               ,self.dev_conf.meta_data["max_adc"]))
        self.pico_status.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.dev_conf.mode["handle"], self.dev_conf.trigger["active"], self.dev_conf.trigger["source"], threshold, 
                                                                        self.dev_conf.trigger["direction"], self.dev_conf.trigger["delay"], self.dev_conf.trigger["auto_trigger_ms"])
        
    def set_channels(self): 
        for chan in self.dev_conf.channels:
            if (self.dev_conf.channels[chan]["active"] == True):
                enable = 1
            else:
                enable = 0
            
            # c = self.dev_conf.channels[chan]
            # self.pico_status.status = ps.ps5000aSetChannel(self.dev_conf.mode["handle"], c["channel_id"], enable, c["coupling"], c["range"], c["offset"])
            # c = self.dev_conf.channels[chan]
            self.pico_status.status["set_channels"] = ps.ps5000aSetChannel(self.dev_conf.mode["handle"], self.dev_conf.channels[chan]["channel_id"], enable, 
                                                           self.dev_conf.channels[chan]["coupling"], self.dev_conf.channels[chan]["range"], self.dev_conf.channels[chan]["offset"])
    
    def run_block(self):
        self.pico_status.status["block_ready"] = ctypes.c_int16(0)
        self.dev_conf.meta_data["total_cap_samples"]=(self.dev_conf.capture["pre_trig_samples"] + self.dev_conf.capture["post_trig_samples"])
        self.dev_conf.meta_data["max_samples"] = ctypes.c_int32(self.dev_conf.meta_data["total_cap_samples"])
        
        self.pico_status.status["run_block"] =  ps.ps5000aRunBlock(self.dev_conf.mode["handle"], self.dev_conf.capture["pre_trig_samples"], 
                                                                   self.dev_conf.capture["post_trig_samples"], self.dev_conf.mode["timebase"], None, 0, None, None)
        while self.pico_status.status["block_ready"].value == self.pico_status.status["block_check"].value:
            self.pico_status.status["is_ready"] =  ps.ps5000aIsReady(self.dev_conf.mode["handle"], ctypes.byref(self.pico_status.status["block_ready"]))
        self.pico_status.status["get_values"] = ps.ps5000aGetValuesBulk(self.dev_conf.mode["handle"], ctypes.byref(self.dev_conf.meta_data["max_samples"]), 0, 
                                                                        (self.dev_conf.capture["n_captures"]-1), 0, 0, ctypes.byref(self.buffer_manager.overflow))
        print(f'block_ready:{self.pico_status.status["block_ready"]} block_check:{self.pico_status.status["block_check"]} run_block:{self.pico_status.status["run_block"]} Get_values:{self.pico_status.status["get_values"]}')

    def stop_scope(self):
        self.pico_status.status["stop"] = ps.ps5000aStop(self.dev_conf.mode["handle"])
        self.pico_status.status["close"] = ps.ps5000aCloseUnit(self.dev_conf.mode["handle"])
        if self.pico_status.status["stop"] == 0:
            self.pico_status.status["open_unit"] = -1




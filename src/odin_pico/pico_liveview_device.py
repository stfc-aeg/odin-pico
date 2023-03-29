import ctypes
from datetime import datetime
import logging
import time
import numpy as np

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc


class PicoLiveView():
    def __init__(self, handle, buffer,buffer_size):
        self.resolution = 1
        self.timebase = 1

        self.handle = ctypes.c_int16(handle)
        self.max_adc = ctypes.c_int16()
        self.samples = buffer_size
        self.max_samples = ctypes.c_int32(self.samples)

        self.buffer = buffer
        self.status = {}

        self.overflow = ctypes.c_int16()
        self.ready = ctypes.c_int16(0)
        self.check = ctypes.c_int16(0)
        #self.overflow = None

        self.samples_per_seg = ctypes.c_int32(0)
    
    def open_unit(self,res):
        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.handle), None, res)
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.handle, ctypes.byref(self.max_adc))
        return self.status["openunit"]
    
    def set_channel(self, channel, en, coupling, range, offset):
        ### Change adapter to store 1/0 instead of true false ?
        enable = None
        if en == True:
            enable = 1
        if en == False:
            enable = 0

        return ps.ps5000aSetChannel(self.handle, channel, enable, coupling, range, offset)

    def set_simple_trigger(self, source, range, threshold_mv, direction, delay, auto_ms ):
        threshold = int(mV2adc(threshold_mv,range,self.max_adc))
        return ps.ps5000aSetSimpleTrigger(self.handle, 1, source, threshold, direction, delay, auto_ms)

    def set_buffer(self, channel, buffer, segment):
        return ps.ps5000aSetDataBuffer(self.handle, channel, buffer[0].ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), self.max_samples, segment, 0)
    
    def set_captures(self, captures):
        #self.status["MemorySegments"] = ps.ps5000aMemorySegments(self.handle, captures, ctypes.byref(self.samples_per_seg))
        self.status["SetNoOfCaptures"] = ps.ps5000aSetNoOfCaptures(self.handle, captures)
        self.overflow = (ctypes.c_int16 * captures)()
        return self.status["SetNoOfCaptures"]

    def initalise_parameters(self):
        self.status["openunit"] = self.open_unit(self.resolution)
        self.status["set_source"] = self.set_channel(0,True,0,9,0.0)
        self.status["set_source"] = self.set_channel(1,False,0,9,0.0)
        self.status["set_source"] = self.set_channel(2,False,0,9,0.0)
        self.status["set_source"] = self.set_channel(3,False,0,9,0.0)
        #self.status["set_trigger"] = self.set_simple_trigger(0,9,0,2,0,10)
        self.status["set_captures"] = self.set_captures(1)
        self.status["set_buffer"] = self.set_buffer(0,self.buffer,0)
        return True

    def run_block(self):
        #print("running capture :)")
        #print(self.status)
        self.status["runblock"] = ps.ps5000aRunBlock(self.handle, 0, self.samples, self.timebase, None, 0, None, None)

        #print(f'Self.ready = {self.ready.value}')
        while self.ready.value == self.check.value:
            self.status["isReady"] = ps.ps5000aIsReady(self.handle, ctypes.byref(self.ready))
        #print(f'Self.ready = {self.ready.value}')

        self.status["GetValuesBulk"] = ps.ps5000aGetValuesBulk(self.handle, ctypes.byref(self.max_samples), 0, 0, 0, 0, ctypes.byref(self.overflow))
        self.ready = ctypes.c_int16(0)

        #print(f'Buffer contents {self.buffer}')

        #print("ran capture :)")
        

    def stop_scope(self):
        self.status["stop"] = ps.ps5000aStop(self.handle)
        self.status["close"] = ps.ps5000aCloseUnit(self.handle)
        return self.status["close"]





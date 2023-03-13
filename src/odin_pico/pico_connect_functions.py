import ctypes
import time
import numpy as np

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

class PicoFunctions():
    def __init__(self, handle):
        self.handle = ctypes.c_int16(handle)
        self.max_adc = ctypes.c_int16()


        # Variables below probably to be removed as functions class changed
        self.n_segments = 3
        self.n_captures = 3

        self.status = {}
        
        self.active_channels = []
        self.channel_ranges = []
        self.channel_buffers = []

        self.res = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]
        print(self.res)
        self.max_adc = ctypes.c_int16()

        self.preTriggerSamples = 400
        self.postTriggerSamples = 100000
        self.maxsamples = self.preTriggerSamples + self.postTriggerSamples
        self.timebase = None

        self.time_interval_actual = ctypes.c_float()
        self.returnedMaxSamples = ctypes.c_int32()

        self.overflow = (ctypes.c_int16 * self.n_segments)()
        self.cmaxSamples = ctypes.c_int32(self.maxsamples)

        self.ready = ctypes.c_int16(0)
        self.check = ctypes.c_int16(0)

        self.Times = (ctypes.c_int64*self.n_segments)()
        self.TimeUnits = ctypes.c_char()

        self.start_time = None
        self.end_time = None

        self.TriggerInfo = None

        #self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.handle), None, self.res)


        # self.status["MemorySegments"] = ps.ps5000aMemorySegments(self.handle, self.n_segments, ctypes.byref(self.cmaxSamples))
        # self.status["SetNoOfCaptures"] = ps.ps5000aSetNoOfCaptures(self.handle, self.n_captures)
    
    def open_unit(self,res):
        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.handle), None, res)
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.handle, ctypes.byref(self.max_adc))
        print("open unit from fujnctions.py: ",self.status["openunit"])
        return self.status["openunit"]
    
    def set_channel(self,status_string, channel, en, coupling, range, offset):
        ps_channel = ps.PS5000A_CHANNEL[channel]
        ps_coupling = ps.PS5000A_COUPLING[coupling]
        ps_range = ps.PS5000A_RANGE[range]

        self.status[status_string] = ps.ps5000aSetChannel(self.handle, ps_channel, en, ps_coupling, ps_range, offset)
        if en == 1:
            self.active_channels.append(channel)
            self.channel_ranges.append(range)

    def set_simple_trigger(self, channel, range, threshold_mv,):
        source = ps.PS5000A_CHANNEL[channel]
        threshold = int(mV2adc(threshold_mv,(ps.PS5000A_RANGE[range]),self.max_adc))
        self.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.handle, 1, source, threshold, 2, 0, 1000)
        print("trigger_status :",self.status["trigger"])


    def generate_buffers(self):
        for i in range(len(self.active_channels)):
            self.channel_buffers.append(np.empty((self.n_captures,self.maxsamples),dtype=np.int16))

        for c,b in zip(self.active_channels,self.channel_buffers):
            print(f'Channel {c}')
            source_chan = ps.PS5000A_CHANNEL[c]
            for i in range(len(b)):
                buffer = b[i]
                self.status[f"SetDataBuffer_{c}_{i}"] = ps.ps5000aSetDataBuffer(self.handle, source_chan, buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), self.maxsamples, i, 0)

    def run_block(self):
        self.status["GetTimebase"] = ps.ps5000aGetTimebase2(self.handle, self.timebase, self.maxsamples, ctypes.byref(self.time_interval_actual), ctypes.byref(self.returnedMaxSamples), 0)
        self.status["runblock"] = ps.ps5000aRunBlock(self.handle, self.preTriggerSamples, self.postTriggerSamples, self.timebase, None, 0, None, None)
        while self.ready.value == self.check.value:
            self.status["isReady"] = ps.ps5000aIsReady(self.handle, ctypes.byref(self.ready))
        self.status["GetValuesBulk"] = ps.ps5000aGetValuesBulk(self.handle, ctypes.byref(self.cmaxSamples), 0, (self.n_segments-1), 0, 0, ctypes.byref(self.overflow))
        self.end_time = time.time()

    def stop_scope(self):
        self.status["stop"] = ps.ps5000aStop(self.handle)
        self.status["close"] = ps.ps5000aCloseUnit(self.handle)

    def run_capture(self):
        print("In functions :):)")
        # self.start_time = time.time()
        # self.generate_buffers()
        # self.run_block()
        # self.stop_scope()

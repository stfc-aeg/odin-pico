import ctypes
from datetime import datetime
import logging
import time
import numpy as np
import h5py

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

class PicoBlockDevice():
    def __init__(self, handle):
        self.handle = ctypes.c_int16(handle)
        self.max_adc = ctypes.c_int16()
        self.max_samples = ctypes.c_int32()
        self.active_channels = []
        self.channel_buffers = []
        self.status = {}
        self.overflow = ctypes.c_int16()
        self.ready = ctypes.c_int16(0)
        self.check = ctypes.c_int16(0)
        self.current_filename = "/tmp/data.hdf5"

        # Initalise set of dictionaries that obtain their keys from using the PicoSDK built in make_enum function
        # To return valid keys for the picoscope values
        self.ps_resolution = {ps.PS5000A_DEVICE_RESOLUTION[val] : val for val in [
            "PS5000A_DR_8BIT",
            "PS5000A_DR_12BIT"
        ]}

        self.ps_coupling = {ps.PS5000A_COUPLING[val] : val for val in [
            "PS5000A_AC",
            "PS5000A_DC"
        ]}

        self.ps_channel = {ps.PS5000A_CHANNEL[val] : val for val in [
            "PS5000A_CHANNEL_A",
            "PS5000A_CHANNEL_B",
            "PS5000A_CHANNEL_C",
            "PS5000A_CHANNEL_D"
        ]}

        self.ps_direction = {ps.PS5000A_THRESHOLD_DIRECTION[val] : val for val in [
            "PS5000A_ABOVE",
            "PS5000A_BELOW",
            "PS5000A_RISING",
            "PS5000A_FALLING",
            "PS5000A_RISING_OR_FALLING"
        ]}

        self.ps_range = {ps.PS5000A_RANGE[val] : val for val in [
            "PS5000A_10MV",
            "PS5000A_20MV",
            "PS5000A_50MV",
            "PS5000A_100MV",
            "PS5000A_200MV",
            "PS5000A_500MV",
            "PS5000A_1V",
            "PS5000A_2V",
            "PS5000A_5V",
            "PS5000A_10V",
            "PS5000A_20V"
        ]}

        self.trigger_dicts = {
            "source":self.ps_channel,
            "direction":self.ps_direction
        }

        self.channel_dicts = {
            "coupling":self.ps_coupling,
            "range":self.ps_range
        }
    
    def open_unit(self,res):
        self.status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(self.handle), None, res)
        self.status["maximumValue"] = ps.ps5000aMaximumValue(self.handle, ctypes.byref(self.max_adc))
        return self.status["openunit"]
    
    def set_channel(self,status_string, channel, en, coupling, range, offset):
        ### Change adapter to store 1/0 instead of true false ?
        enable = None
        if en == True:
            enable = 1
        if en == False:
            enable = 0

        self.status[status_string] = ps.ps5000aSetChannel(self.handle, channel, enable, coupling, range, offset)
        print(f'Set channel status of {status_string} = {self.status[status_string]}, values to : {self.handle, channel, enable, coupling, range, offset} ')

        if enable == 1:
            self.active_channels.append(channel)

    def set_simple_trigger(self, source, range, threshold_mv, direction, delay, auto_trigger):
        threshold = int(mV2adc(threshold_mv,range,self.max_adc))
        self.status["trigger"] = ps.ps5000aSetSimpleTrigger(self.handle, 1, source, threshold, direction, delay, auto_trigger)

    def generate_buffers(self,captures):
        for i in range(len(self.active_channels)):
            self.channel_buffers.append(np.zeros(shape=(captures,np.int32(self.max_samples)),dtype=np.int16))

        for c,b in zip(self.active_channels,self.channel_buffers):
            for i in range(len(b)):
                buffer = b[i]
                self.status[f"SetDataBuffer_{c}_{i}"] = ps.ps5000aSetDataBuffer(self.handle, c, buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), self.max_samples, i, 0)

        # Attempt at fixing status code 13

        # print(f'Active channels:{self.active_channels} | Number of captures:{captures} | total Samples per capture:{max_samples} ')

        # for chan in range(len(self.active_channels)):
        #     self.channel_buffers.append(np.empty((captures,np.int32(max_samples)),dtype=np.int16))
        #     print(f'Generated buffer holding np.array for {chan} : {self.channel_buffers[chan]}')

        #     for buff in range(len(self.channel_buffers)):
        #         cur_buff = self.channel_buffers[buff]
        #         self.status[f'set_data_buffer_{chan}_{buff}'] = ps.ps5000aSetDataBuffer(self.handle, chan, cur_buff.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), max_samples, buff, 0)


    def run_block(self,timebase,pre_trig_samples,post_trig_samples,captures):
        self.current_filename = (('/tmp/')+(str(datetime.now())).replace(' ','_')+'.hdf5')
        self.max_samples = ctypes.c_int32(pre_trig_samples + post_trig_samples)
        samples_per_seg = ctypes.c_int32(0)
        self.overflow = (ctypes.c_int16 * captures)()

        self.status["MemorySegments"] = ps.ps5000aMemorySegments(self.handle, captures, ctypes.byref(samples_per_seg))
        self.status["SetNoOfCaptures"] = ps.ps5000aSetNoOfCaptures(self.handle, captures)
        self.generate_buffers(captures)
        self.status["runblock"] = ps.ps5000aRunBlock(self.handle, pre_trig_samples, post_trig_samples, timebase, None, 0, None, None)

        while self.ready.value == self.check.value:
            self.status["isReady"] = ps.ps5000aIsReady(self.handle, ctypes.byref(self.ready))
        self.status["GetValuesBulk"] = ps.ps5000aGetValuesBulk(self.handle, ctypes.byref(self.max_samples), 0, (captures-1), 0, 0, ctypes.byref(self.overflow))

        self.write_to_file()

    def write_to_file(self):

        ### Items needed for converting ADC counts back to mv and plotting time values ###
        # - buffer of data 
        # - individual channel range
        # - maxADC of whole system
        # - sample interval in ns
        # - maxsamples (can probably be gotten from the length of the dataset once reading the file and doesnt need to be saved)
        
        metadata = {

            #'max_adc': self.max_adc,
            'active_channels': self.active_channels[:],
            #'channel_ranges': self.channel_ranges[:]
        }

        with h5py.File(self.current_filename,'w') as f:
            metadata_group = f.create_group('metadata')
            for key, value in metadata.items():
                metadata_group.attrs[key] = value

            for c,b in zip(self.active_channels,self.channel_buffers):

                f.create_dataset(('adc_counts_'+str(c)), data = b)
                print(f'Creating dataset: adc_counts_{str(c)} with data : {b}')

        logging.debug(f'File writing complete')

    def stop_scope(self):
        self.status["stop"] = ps.ps5000aStop(self.handle)
        self.status["close"] = ps.ps5000aCloseUnit(self.handle)
        return self.status["close"]


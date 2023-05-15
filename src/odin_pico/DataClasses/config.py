from dataclasses import dataclass, field
from typing import List
import ctypes
from odin_pico.pico_util import PicoUtil

@dataclass
class channel:
    channel_id: int
    name: str
    active: bool = False
    verified: bool = False
    coupling: int = 0 
    range: int = 0
    offset: float = 0.0

    def reset(self):
        self.active = False
        self.verified = False
        self.coupling = 0 
        self.range = 0
        self.offset = 0.0




@dataclass
class DeviceConfig:
    num_channels: int = 0


util = PicoUtil()


config = DeviceConfig()

channels = {}

i = 0
for name in util.channel_names:
    channels[name] = channel(i,name)
    i += 1
    
    #chan = getattr(config,name)
    #config.name = channel(name,i)
    #setattr(config,name,channel(name,i))
    #setattr(chan,f'channel_{name}',i)
## config = DeviceConfig(dict of created channel objects?)



##########################################
# Testing overloading dataclass instance 

test_dict = {
    "pre_trig_samples": 0,
    "post_trig_samples": 0,
    "n_captures": 0
}

config = DeviceConfig()

print(config)
#config.test = "Added after creation"
setattr(config,'test',"Testing")
print(config)



    


######################################
# Testing - creating a data class with arguments
# - giving it methods, ie to reset values
# test = DeviceConfig(0,"a")
# print(test)

# test.coupling = 9
# test.range = 5

# print(test)

# #test = DCTest(test.channel_id,test.name)
# test.reset()

# print(test)
######################################
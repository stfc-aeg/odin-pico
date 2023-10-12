from dataclasses import dataclass, field
from picosdk.ps5000a import ps5000a as ps

from odin_pico.pico_util import PicoUtil

@dataclass
class Channel:
    channel_id: int
    name: str
    active: bool = False
    verified: bool = False
    coupling: int = 0
    range: int = 0
    offset: float = 0.0

    def default_channel_configs():
        return {name: Channel(id, name) for (id, name) in enumerate(['A', 'B', 'C', 'D'])}
    
@dataclass
class Person:
    name: str
    age: int = field(init=False)
    location: int

    util = PicoUtil()

    def __init__(self):
        self.name = "test"
        self.age = 37
        self.location = 0

        

        print(self.util.ps_direction)

    @property
    def age(self) -> int:
        return self._age
    
    @property
    def location(self) -> int:
        return self._location

    @age.setter
    def age(self, value: int):
        if value < 0:
            raise ValueError("Age cannot be negative.")
        self._age = value
    
    @location.setter
    def location(self, value:int):
        if value in self.util.ps_direction:  #[0,1,2,3,4]
            self._location = value
        else:
            print("location out of bounds")

@dataclass
class DeviceConfig:
    def __init__(self):
        # Add each ChannelConfig as a field using set attribute
        print(Channel.default_channel_configs())
        for name, channel in Channel.default_channel_configs().items():
            setattr(self, f'channel_{name}', channel)

        self.person = Person()


    @property
    def num_channels(self):
        return len([attr for attr in dir(self) if attr.startswith("channel_")])

    @property
    def channel_names(self):
        return [attr.split('_')[-1] for attr in dir(self) if attr.startswith("channel_")]








def main():
    device = DeviceConfig()

    print(device.person)
    device.channel_A.offset = 1.0
    device.channel_B.range = 5
    #print(device.channel_A)
    print("dataclasses no_dict config")
    #print(f"Device config has {device.num_channels} channels with names: {', '.join(device.channel_names)}")
    #print(device.channel_A.channel_id)
    print()
    print(f'A:{device.channel_A}\nB:{device.channel_B}\nC:{device.channel_C}\nD:{device.channel_D}')
    print(f'Channel B range: {device.channel_B.range}')
    device.person.location = 3
    device.person.location = 5
    print(device.person)

    device.channel_A.reset()
    print(device.channel_A)



if __name__ == '__main__':
    main()
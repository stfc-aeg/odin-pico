from dataclasses import dataclass, field

@dataclass
class Channel:
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

    def default_channel_configs():
        return {name: Channel(id, name) for (id, name) in enumerate(['A', 'B', 'C', 'D'])}

@dataclass
class DeviceConfig:
    def __init__(self):
        # Add each ChannelConfig as a field using set attribute
        print(Channel.default_channel_configs())
        for name, channel in Channel.default_channel_configs().items():
            setattr(self, f'channel_{name}', channel)

    @property
    def num_channels(self):
        return len([attr for attr in dir(self) if attr.startswith("channel_")])

    @property
    def channel_names(self):
        return [attr.split('_')[-1] for attr in dir(self) if attr.startswith("channel_")]








def main():
    device = DeviceConfig()

    device.channel_A.offset = 1.0
    device.channel_B.range = 5
    #print(device.channel_A)
    print("dataclasses no_dict config")
    #print(f"Device config has {device.num_channels} channels with names: {', '.join(device.channel_names)}")
    #print(device.channel_A.channel_id)
    print()
    print(f'A:{device.channel_A}\nB:{device.channel_B}\nC:{device.channel_C}\nD:{device.channel_D}')
    print(f'Channel B range: {device.channel_B.range}')

if __name__ == '__main__':
    main()
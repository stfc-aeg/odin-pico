from dataclasses import dataclass, field


@dataclass
class ChannelConfig:
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
        return {
            name: ChannelConfig(id, name)
            for (id, name) in enumerate(["A", "B", "C", "D"])
        }


@dataclass
class DeviceConfig:
    channel_config: dict[str, ChannelConfig] = field(
        default_factory=ChannelConfig.default_channel_configs
    )

    @property
    def num_channels(self):
        return len(self.channel_config)

    @property
    def channel_names(self):
        return list(self.channel_config.keys())


def main():
    device = DeviceConfig()

    # for channel in device.channel_names:
    # print(device.channel_config[channel])

    device.channel_config["A"].offset = 1.0

    # print(device.channel_config['A'])

    print(device)


if __name__ == "__main__":
    main()

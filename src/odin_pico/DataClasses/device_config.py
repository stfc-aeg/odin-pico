import ctypes
import json
import os
from dataclasses import asdict, dataclass, field

from odin_pico.DataClasses.capture_config import CaptureConfig
from odin_pico.DataClasses.capture_run_config import CaptureRunConfig
from odin_pico.DataClasses.channel_config import ChannelConfig
from odin_pico.DataClasses.file_config import FileConfig
from odin_pico.DataClasses.meta_data import MetaDataConfig
from odin_pico.DataClasses.mode_config import ModeConfig
from odin_pico.DataClasses.pha_config import PHAConfig
from odin_pico.DataClasses.trigger_config import TriggerConfig


@dataclass
class DeviceConfig:
    preview_channel: int = 0
    config_folder_path: str = "/tmp/configs/"
    capture_folder_path: str = "/tmp/captures/"
    channel_names: list[str] = field(default_factory=list)
    mode: ModeConfig = field(default_factory=ModeConfig)
    trigger: TriggerConfig = field(default_factory=TriggerConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    capture_run: CaptureRunConfig = field(default_factory=CaptureRunConfig)
    meta_data: MetaDataConfig = field(default_factory=MetaDataConfig)
    file: FileConfig = field(default_factory=FileConfig)
    pha: PHAConfig = field(default_factory=PHAConfig)

    def __post_init__(self):
        for name, channel in ChannelConfig.default_channel_configs().items():
            setattr(self, f"channel_{name}", channel)
            self.channel_names.append(name)

    ## Config saving is not fully implemented and so these functions will be passed if called
    def pre_save_adjustment(self):
        return
        """
            Removes ctypes from the variables that store them, as these have issues being serialised
            Removes the PicoUtil object from being saved to file, this is not needed 
        """
        conf_d = asdict(self)
        conf_d["mode"]["handle"] = int(self.mode.handle.value)
        conf_d["meta_data"]["max_adc"] = int(self.meta_data.max_adc.value)
        conf_d["meta_data"]["max_samples"] = int(self.meta_data.max_samples.value)
        conf_d["meta_data"]["total_cap_samples"] = int(
            self.meta_data.total_cap_samples.value
        )
        conf_d["meta_data"]["samples_per_seg"] = int(
            self.meta_data.samples_per_seg.value
        )

        for name in ["A", "B", "C", "D"]:
            if f"channel_{name}" in conf_d:
                del conf_d[f"channel_{name}"]["util"]

        return conf_d

    def post_load_adjustment(self, data):
        return
        """
            Adds back in ctypes dependencies were they are needed
        """
        data["mode"]["handle"] = ctypes.c_int16(data["mode"]["handle"])
        data["meta_data"]["max_adc"] = ctypes.c_uint16(data["meta_data"]["max_adc"])
        data["meta_data"]["max_samples"] = ctypes.c_int32(
            data["meta_data"]["max_samples"]
        )
        data["meta_data"]["total_cap_samples"] = ctypes.c_int32(
            data["meta_data"]["total_cap_samples"]
        )
        data["meta_data"]["samples_per_seg"] = ctypes.c_int32(
            data["meta_data"]["samples_per_seg"]
        )

    def save_to_file(self, config_name):
        return
        if not os.path.exists(self.folder_path):
            os.mkdir(self.folder_path)

        full_path = os.path.join(self.folder_path, f"{config_name}.json")
        with open(full_path, "w") as f:
            json.dump(self.pre_save_adjustment(), f)

    def load_from_file(self, config_name):
        return
        if os.path.exists(self.folder_path):
            full_path = os.path.join(self.folder_path, f"{config_name}.json")
            if os.path.isfile(full_path):
                with open(full_path) as f:
                    config_data = json.load(f)
                self.post_load_adjustment(config_data)

                # Error handling for if the loaded data doesn't map on to the dataclass objec
                # set self.X to equal new object with the default values of X
                self.mode = (
                    ModeConfig(**config_data["mode"])
                    if "mode" in config_data
                    else ModeConfig()
                )
                self.trigger = (
                    TriggerConfig(**config_data["trigger"])
                    if "trigger" in config_data
                    else TriggerConfig()
                )
                self.capture = (
                    CaptureConfig(**config_data["capture"])
                    if "capture" in config_data
                    else CaptureConfig()
                )
                self.capture_run = (
                    CaptureRunConfig(**config_data["capture_run"])
                    if "capture_run" in config_data
                    else CaptureRunConfig()
                )
                self.meta_data = (
                    MetaDataConfig(**config_data["meta_data"])
                    if "meta_data" in config_data
                    else MetaDataConfig()
                )
                self.file = (
                    FileConfig(**config_data["file"])
                    if "file" in config_data
                    else FileConfig()
                )
                self.pha = (
                    PHAConfig(**config_data["pha"])
                    if "pha" in config_data
                    else PHAConfig()
                )
                self.preview_channel = config_data.get("preview_channel", 0)

                for name in ["A", "B", "C", "D"]:
                    channel_data = config_data.get(f"channel_{name}")
                    if channel_data:
                        channel = ChannelConfig(**channel_data)
                        setattr(self, f"channel_{name}", channel)
        else:
            os.mkdir(self.folder_path)


def main():
    # return
    device = DeviceConfig()
    name = "C"
    print(device.get_dc_value(device, f"channel_{name}", "channel_id"))

    return

    print(f"channel_names: {device.channel_names}")
    print(f"Trigger setting before set_value: {device.trigger.active}")
    device.channel_names.append("A")
    device.channel_A.offset = 1.0
    device.channel_B.range = 5
    print(f"channel_names: {device.channel_names}")

    print(f"Trigger setting after set_value: {device.trigger.active}")


if __name__ == "__main__":
    main()

from odin_pico.pico_util import PicoUtil

class DeviceConfig():
    def __init__(self):
        self.util = PicoUtil()

        self.mode = self.util.set_mode_defaults()
        self.trigger = self.util.set_trigger_defaults()
        self.capture = self.util.set_capture_defaults()
        self.channels = {}
        i = 0
        for name in self.util.channel_names:
            self.channels[name] = self.util.set_channel_defaults(name,i)
            i += 1
        
        self.meta_data = self.util.set_meta_data_defaults()


# test = DeviceConfig()
# path = "trigger"
# print(f'Connection:{test.connection} \nTrigger:{getattr(test,path)["active"]}\nChannels:{test.channels}')



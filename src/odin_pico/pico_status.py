from odin_pico.pico_util import PicoUtil

class Status():
    def __init__(self):
        self.util = PicoUtil()

        self.flag = self.util.set_flag_defaults()
        self.status = self.util.set_status_defaults()
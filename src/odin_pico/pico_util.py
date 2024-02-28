import math

from picosdk.ps5000a import ps5000a as ps


class PicoUtil:
    def __init__(self):
        ######
        # Revisit to see if channels_names, channel_names_dict and ps_channels can be replaced with just ps_channels
        self.channel_names = ["a", "b", "c", "d"]
        self.channel_names_dict = {0: "a", 1: "b", 2: "c", 3: "d"}
        ######

        self.range_offsets = {
            0: 0.25,
            1: 0.25,
            2: 0.25,
            3: 0.25,
            4: 0.25,
            5: 2.5,
            6: 2.5,
            7: 2.5,
            8: 20,
            9: 20,
            10: 20,
        }

        self.ps_resolution = {
            ps.PS5000A_DEVICE_RESOLUTION[val]: val
            for val in ["PS5000A_DR_8BIT", "PS5000A_DR_12BIT"]
        }

        self.ps_coupling = {
            ps.PS5000A_COUPLING[val]: val for val in ["PS5000A_AC", "PS5000A_DC"]
        }

        self.ps_channel = {
            ps.PS5000A_CHANNEL[val]: val
            for val in [
                "PS5000A_CHANNEL_A",
                "PS5000A_CHANNEL_B",
                "PS5000A_CHANNEL_C",
                "PS5000A_CHANNEL_D",
            ]
        }

        self.ps_direction = {
            ps.PS5000A_THRESHOLD_DIRECTION[val]: val
            for val in [
                "PS5000A_ABOVE",
                "PS5000A_BELOW",
                "PS5000A_RISING",
                "PS5000A_FALLING",
                "PS5000A_RISING_OR_FALLING",
            ]
        }

        self.ps_range = {
            ps.PS5000A_RANGE[val]: val
            for val in [
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
                "PS5000A_20V",
            ]
        }

        self.trigger_dicts = {"source": self.ps_channel, "direction": self.ps_direction}

        self.channel_dicts = {"coupling": self.ps_coupling, "range": self.ps_range}

        self.mode_dicts = {"resolution": self.ps_resolution}

    def get_range_value_mv(self, key):
        range_values = {
            0: 10,
            1: 20,
            2: 50,
            3: 100,
            4: 200,
            5: 500,
            6: 1000,
            7: 2000,
            8: 5000,
            9: 10000,
            10: 20000,
        }
        if key in range_values:
            return range_values[key]

    def get_time_unit(self, key):
        unit_values = {0: -15, 1: -12, 2: -9, 3: -6, 4: -3, 5: 0}
        if key in unit_values:
            return unit_values[key]

    def verify_mode_settings(self, chan_active, mode):
        channel_count = 0

        for chan in chan_active:
            if chan == True:
                channel_count += 1

        if mode.resolution == 1:
            if mode.timebase < 1:
                return -1
            elif mode.timebase == 1 and channel_count > 0 and channel_count < 2:
                return 0
            elif mode.timebase == 2 and channel_count > 0 and channel_count < 3:
                return 0
            elif mode.timebase >= 3 and channel_count > 0 and channel_count <= 4:
                return 0
            else:
                return -1

        if mode.resolution == 0:
            if mode.timebase < 0:
                return -1
            elif mode.timebase == 0 and channel_count > 0 and channel_count < 2:
                return 0
            elif mode.timebase == 1 and channel_count > 0 and channel_count < 3:
                return 0
            elif mode.timebase >= 2 and channel_count > 0 and channel_count <= 4:
                return 0
            else:
                return -1

        if channel_count == 0:
            return -1

    def verify_channel_settings(self, offset):
        if (offset >= 0) and (offset <= 100):
            return True
        else:
            return False

    def set_channel_verify_flag(self, channels):
        error_count = 0
        for chan in channels:
            if (chan.active == True) and (chan.verified == False):
                error_count += 1
        if error_count == 0:
            return 0
        else:
            return -1

    def verify_trigger(self, channels, trigger):
        source_chan = channels[trigger.source]
        if not (source_chan.active):
            return -1
        if trigger.threshold > self.get_range_value_mv(source_chan.range):
            return -1
        if not (trigger.delay >= 0 and trigger.delay <= 4294967295):
            return -1
        if not (trigger.auto_trigger_ms >= 0 and trigger.auto_trigger_ms <= 32767):
            return -1
        return 0

    def verify_capture(self, capture):
        total_samples = capture.pre_trig_samples + capture.post_trig_samples
        if total_samples < 1:
            return -1
        if capture.n_captures < 1:
            return -1
        return 0

    def calc_offset(self, range, off_per):
        try:
            range_mv = self.get_range_value_mv(range)
            return (math.ceil(range_mv / (100 / off_per))) * pow(10, -3)
        except:
            return 0

    def max_samples(self, resolution):
        if resolution == 0:
            return (512) * 10**6
        elif resolution == 1:
            return (256) * 10**6
        else:
            return None

    def flatten_metadata_dict(self, d):
        """Function to flatten a dictionary structure, whilst maintaining
        a unique name for each value in the dictionary, returns a dict
        """
        flat_d = {}
        for key, value in d.items():
            if isinstance(value, dict):
                # If the value is a nested dictionary, append the dict_key as a prefix to the keys
                dict_key = key
                for inner_key, inner_value in value.items():
                    # If the value is not a PicoUtil object add it to the dict, else, skip it
                    if not isinstance(inner_value, PicoUtil):
                        flattened_key = f"{dict_key}_{inner_key}"
                        flat_d[flattened_key] = inner_value
            elif not isinstance(value, PicoUtil):
                flat_d[key] = value
        return flat_d

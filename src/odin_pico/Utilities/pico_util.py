import math
import logging
import numpy as np

from picosdk.ps5000a import ps5000a as ps
from odin.adapters.adapter import ApiAdapterRequest

class PicoUtil:
    """Class containing several functions, useful for the PicoScope."""

    def __init__(self):
        """Initialise the PicoUtil class."""
        # Revisit to see if channels_names, channel_names_dict are obsolete.
        self.channel_names = ["a", "b", "c", "d"]
        self.channel_names_dict = {0: "a", 1: "b", 2: "c", 3: "d"}

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
        """Convert channel ranges from a key to an actual range."""
        range_values = {
            0: 10, 1: 20, 2: 50, 3: 100, 4: 200, 5: 500,
            6: 1000,7: 2000, 8: 5000, 9: 10000, 10: 20000,
        }
        if key in range_values:
            return range_values[key]

    def get_time_unit(self, key):
        """Retrieve the time unit from the key."""
        unit_values = {0: -15, 1: -12, 2: -9, 3: -6, 4: -3, 5: 0}
        if key in unit_values:
            return unit_values[key]

    def calc_offset(self, range, off_per):
        """Calculate the offset, depending on range of channel."""
        try:
            range_mv = self.get_range_value_mv(range)
            return((math.ceil(range_mv/(100/off_per)))*pow(10,-3))
        except:
            return 0

    def max_samples(self, resolution):
        """Calculate the maximum amount of captures per run."""
        if resolution == 0:
            return (512) * 10**6
        elif resolution == 1:
            return (256) * 10**6
        else:
            return None

    def flatten_metadata_dict(self, d):
        """Flatten a dictionary structure, maintaining a unique name for each value."""
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
    
    @staticmethod
    def adc2mV(bufferADC, range, maxADC):
        """
        Convert a buffer of raw ADC count values into millivolts.
        
        :param bufferADC : numpy.ndarray or list/array-like Buffer of raw ADC count values (int16)
        :param range : Index into the channelInputRanges list
        :param maxADC : c_uint16 Maximum ADC count value
        
        :return: numpy.ndarray or list Buffer values converted to millivolts (float64)
        """
        channelInputRanges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]
        vRange = channelInputRanges[range]
        
        # Division in Python 3 returns a float, avoiding any integer overflow
        scaling_factor = vRange / maxADC.value
        
        # Check if the input is a NumPy array
        if isinstance(bufferADC, np.ndarray):
            # Apply the scaling factor to the entire array at once
            # Convert to float64 before any calculations to avoid overflow
            bufferV = bufferADC.astype(np.float64) * scaling_factor
        else:
            # For non-NumPy arrays (lists, C arrays, etc.), use list comprehension
            # Explicitly convert each value to float before any operations
            # Return a regular Python list of float values
            bufferV = [float(x) * scaling_factor for x in bufferADC]
        
        return bufferV
    

    def iac_get(self, adapter, path, **kwargs):
        """Generic inter-adapter-communication get method for odin_control adapters.
        
        This method handles sending an HTTP style GET request to another adapter using the 
        targets GET method implementation to request a value from its parameter tree. 

        :param adapter: Adapter object to target
        :param path: Parameter tree path to target, must also include the parameter itself
        :param **kwargs as_dict: Used to tell the function to return the response as a dict
        :return: Value of the parameter requested, or {param:value}

        Example usage :\n
        iac_get(self.adapters.munir, 'subsystems/babyd/status/executing', as_dict=True)\n
        iac_get(self.adapters.munir, 'subsystems/babyd/status/executing')\n
        """
        as_dict = kwargs.get('as_dict', False)
        param = path.split('/')[-1]
        request = ApiAdapterRequest(None, accept="application/json")
        response = adapter.get(path, request)
        if response.status_code != 200:
            logging.debug(f"IAC GET failed for adapter {adapter}, path {path}: {response.data}")
        return response.data if as_dict else response.data.get(param)

    def iac_set(self, adapter, path, *args):
        """Generic inter-adapter-communication set method for odin_control adapters.
        
        This method handles sending an HTTP style PUT request to another adapter using the target's
        PUT method implementation to update its parameter tree values.

        :param adapter: Adapter object to target
        :param path: Parameter tree path to target, to not include the parameter itself
        :param *args: Accepts either a key-value pair (param, data) or a dictionary of key-value pairs
        :return: The response object from the target

        Example usage :\n
        self.iac_set(self.adapters.munir, 'args/', 'file_path', '/tmp')\n
        self.iac_set(self.adapters.munir, 'args/', {'file_path':'/tmp/josh/', 'file_name':'test_01_josh'})\n
        For values at the root of the tree provide an empty string as the path
        """
        # Check if the first argument is a dictionary
        if len(args) == 1 and isinstance(args[0], dict):
            data_dict = args[0]
        elif len(args) == 2:
            param, data = args
            data_dict = {param: data}
        else:
            logging.error("Invalid arguments provided. Provide either (param, data) or a dictionary of values.")
            return

        # Create the request with the constructed data dictionary
        request = ApiAdapterRequest(data_dict, content_type="application/vnd.odin-native")
        response = adapter.put(path, request)
        if response.status_code != 200:
            logging.error(f"IAC SET failed for adapter {adapter}, path {path}: {response.data}")
        return response.data
    

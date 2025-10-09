# GPIB temperature control integration

This markdown explains how the odin-gpib package is integrated into the odin-pico package. 

## Installation

The GPIB dependencies of this project can be installed using the pyproject.toml optional dependencies, which is specified as:

[project.optional-dependencies]
```ini
gpib = [
    "odin-gpib @ git+https://github.com/stfc-aeg/odin-gpib@main"
]
```

When installing the odin-pico package you can do:

```shell
pip install .[gpib]
```

This will install the optional odin-gpib package, its dependencies and make its adapter available.




## Initialisation

### Config

The GPIB aspect of this package is entirely optional and the system works with/without it enabled. The GPIB adapter is initilised by simply specifying the adapter in the odin_control.cfg file used. 

For example:

```ini
# excerpt from the ODIN server config
adapters = pico, gpib
....
[adapter.gpib]
module = odin_gpib.adapter.GpibAdapter
background_task_enable = 0
```

### Adapter

Within PicoController.initialize_adapters(), the funciton is given a list of current running adapters, if the gpib adapter has been initilised it will be passed to this function, and a reference saved to self.
```python
self.gpib = adapters['gpib'] if adapters else None
```

Here the function will attempt to find any K2510 devices. These are TEC(Thermo-Electric_cooler)Controllers, which are used for temperature control of the samples being analyised in the AlphaSpec system.
```python
devices = self.util.iac_get(self.gpib, "devices")
self.gpib_config.tec_devices = [name for name, info in devices.items()
    if info.get("type") == "K2510"]
```

It will confirm that things like drivers are installed and that the device is ready to use by calling the verify_gpib_avail() function, the self.gpib_config.avail is used as a guard when performing GPIB related tasks to decide wether to do them or not. 
```python
self.gpib_config.avail = self.ctrl_util.verify_gpib_avail()
```

If a device(s) have been found and added to the list of tec_devices the first one found will be automatically selected (The system is unlikely to ever be used with multiple TEC-Controllers, so the first one found is usually the only one, hence it is automatically selected)
```python
if self.gpib_config.tec_devices:
    self.gpib_config.selected_tec = self.gpib_config.tec_devices[0]
```

Both the Picoscope and GPIB paramtrees are then created.
The create_gpib_tree() funciton will use the gpib_avail and tec_devices list to create a parameter tree that will be able to control any connected devices if they're connected, or provide a basic empty tree which just states that the GPIB functionality is not available.


### UI

The UI will automatically hide/show GPIB related inputs and controls if they exist. This uses the .avail parameter exposed in the paramtree:

```javascript
if (response.gpib && response.gpib.gpib_avail === true) {
    setGpibEnabled(true);
} else {
    setGpibEnabled(false);
}
```


## Usage and Functionality

Capture modes enabled by GPIB integration

When the GPIB functionality is available and a TEC device has been detected, the system has two additional capture modes. This is further controlled by the user with the gpib_control enable/disable parameter which can be used to toggle the funcitonality on/off when its available. 

### Single-Shot Temperature Capture

This mode allows a user to manually set a single target temperature and wait for the TEC to stabilise before starting a capture. This mode is used for one-off acquisitions where the user wants a capture at a single controlled temperature.

- User enters a value into the temp target
- User presses a button connected to the /gpib/set/set_temp parameter, which starts the temperature setting on the TEC-controller
- The PicoController enters a “waiting for TEC to stabilise” state while background polling checks that the measured temperature has settled within tolerance (tol).
- Once stable, the PicoScope capture begins automatically.


### Temperature-Sweep Capture

The temperature-sweep mode automates a sequence of captures across a range of temperatures, as defined in the parameter tree section /gpib/temp_sweep.

Users can configure:

- t_start – starting temperature
- t_end – final temperature
- t_step – increment between points
- tol – stability tolerance
- poll_s – polling interval for temperature readings

When the sweep is activated (active = true), the run_capture in the PicoController will:

- Generate a list of temperatures to capture at, based on the start-end and step parameters
- Step through each temperature in the range and wait for it to stabilise
- Trigger a PicoScope capture at that temperature
- Append a temperature suffix (e.g. _25-0c) to the output filename

This results in a series of files, for example:

capture_20-0c.hdf5, capture_25-0c.hdf5, capture_30-0c.hdf5











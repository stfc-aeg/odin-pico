# odin-pico
Python package based on odin-control to manage a picoscope 5444D

<br><br>

# Installing GPIB functionality

Refer to /docs/GPIB_integration.md for instructions

# Running the UI

Download the app.build from odin-pico either .tgz or .zip


## .tgz

```shell
curl -L -o app_build.tgz https://github.com/stfc-aeg/odin-pico/releases/download/1.3.0/app_build.tgz
```
Replace 1.3.0 with the latest release

Move that file to web/static

Run
```shell
tar -xvzf app_build.tgz
```

Delete the leftover .tgz file


## .zip

```shell
curl -L -o app_build.zip https://github.com/stfc-aeg/odin-pico/releases/download/1.3.0/app_build.zip
```
Replace 1.3.0 with the latest release

Move that file to web/static

Extract the zip file

Delete the leftover .zip file

<br><br>

### Finaly


Change the name of the new dist file and the name on the .cfg file in web/config to match
static_path = web/static/{NEW_NAME}

Run the server using the config file you changed
e.g:
```shell
odin_control --config web/config/odin_pico_dev09_react.cfg
```
# odin-pico
- Python package based on odin-control to manage a picoscope 5444D

<br>

# Running the UI

- Navigate to `odin-pico/odin-pico-react/`
- Run `npm run build`
- Move the `dist` folder to `odin-pico/web/static/

<br>

# Installing GPIB functionality

- Refer to /docs/GPIB_integration.md for instructions

<br>

# Installing GPIO functionality

- Ensure your GPIO is running the server code from here: [odin-gpio/server](https://github.com/stfc-aeg/odin-gpio/tree/server-code)
- Install the GPIO client adapter from here: [odin-gpio/client](https://github.com/stfc-aeg/odin-gpio/tree/client-code)
- Ensure the adapter is being used by the odin-pico instance:
    ```
    [adapter.gpio-server]
    module = odin_gpio_server.adapter.GpioServerAdapter
    ```

import { OdinGraph } from 'odin-react';
import React from 'react';

const sourceOptions = [
  { value: 0, label: 'Channel A' },
  { value: 1, label: 'Channel B' },
  { value: 2, label: 'Channel C' },
  { value: 3, label: 'Channel D' },
];

const channelIdToKey = {
  0: 'a',
  1: 'b',
  2: 'c',
  3: 'd',
};

const rangeValueToMilliVolts = {
  '0': 10,
  '1': 20,
  '2': 50,
  '3': 100,
  '4': 200,
  '5': 500,
  '6': 1000,
  '7': 2000,
  '8': 5000,
  '9': 10000,
  '10': 20000,
};

const generateXValues = (start_x, y_array, step = 1) =>
    Array.from({ length: y_array.length }, (_, i) => start_x + i * step);

const CurrentPHA = ({ pico_endpoint, EndpointCheckbox, canRun }) => {
    let lv_data = pico_endpoint?.data?.device?.live_view?.lv_data;
    if (lv_data == undefined) {
        return (
            <div>Loading live data...</div>
        );
    }

    let pre_trig_samples = -Math.abs(pico_endpoint?.data?.device?.settings?.capture?.pre_trig_samples);
    let post_trig_samples = -Math.abs(pico_endpoint?.data?.device?.settings?.capture?.post_trig_samples);
    const lv_active_channels = pico_endpoint?.data?.device?.live_view?.lv_active_channels;
    const device_settings = pico_endpoint?.data?.device?.settings;

    let series_names = ["Loading..."]

    series_names = lv_active_channels.map(ch => {
        const found = sourceOptions.find(opt => opt.value === ch);
        return found ? found.label : String(ch);
    });

    const prepared_data = lv_data.slice(0, 2).map((y_array, idx) => {
        const x_array = generateXValues(pre_trig_samples, y_array);
        const channel_name = series_names[idx] || `Channel ${idx}`;
        const trace = {
            x: x_array,
            y: y_array,
            name: channel_name,
        };

        // If it is the second channel (index 1), attach to y2 axis
        if (idx === 1) {
            trace.yaxis = 'y2';
        }

        return trace;
    });

    const getChannelRange = (device_settings, lv_active_channels, index) => {
        if (!device_settings || !lv_active_channels || lv_active_channels.length <= index) {
            return 0;
        }
        const ch_id = lv_active_channels[index];
        const ch_key = channelIdToKey[ch_id];
        const ch_range = device_settings.channels?.[ch_key].range;
        const yrange = rangeValueToMilliVolts[ch_range];

        return [-yrange, yrange];
    };

    const layout = {
        xaxis: {
            title: { text: 'Sample Interval' },
            range: [{pre_trig_samples}, {post_trig_samples}]
        },
        yaxis: {
            title: { text: (prepared_data[0]?.name+" Voltage (mV)")},
            range: getChannelRange(device_settings, lv_active_channels, 0)
        },
        yaxis2: {
            title: { text: (prepared_data[1]?.name+" Voltage (mV)")},
            overlaying: 'y',
            side: 'right',
            visible: lv_data.length === 2,
            range: getChannelRange(device_settings, lv_active_channels, 1)
        },
        title: {
            text: 'Live View of PicoScope Traces'
        },
        margin: {
            t: 40,
            b: 40,
            l: 50,
            r: 50
        },
        legend: {
            orientation: 'h',
            y: -0.2,
            x: 0,
            xanchor: 'left',
        },
    };

    if (prepared_data.length === 0) {
        prepared_data.push(0);
    }

    const channels = ['a', 'b', 'c', 'd'];

    return (
        <>
            <span>&nbsp;&nbsp;Select Live View Channels: &nbsp;</span>

            {channels.map((ch) => (
                <React.Fragment key={ch}>
                    <EndpointCheckbox
                        id={`channel-${ch}-liveview`}
                        endpoint={pico_endpoint}
                        fullpath={`device/settings/channels/${ch}/live_view`}
                        disabled={!canRun[ch]}
                    />
                    &nbsp;{ch.toUpperCase()}&nbsp;&nbsp;
                </React.Fragment>
            ))}

            <OdinGraph
                style={{ width: '100%', height: '100%' }}
                useResizeHandler={true}
                data={prepared_data}
                layout={layout}
            />
        </>
    )
}


export default CurrentPHA
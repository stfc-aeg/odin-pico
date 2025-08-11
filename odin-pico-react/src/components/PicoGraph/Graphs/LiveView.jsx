import { OdinGraph } from 'odin-react';
import React, {useState, useEffect} from 'react';
import UICard from '../../utils/UICard';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const sourceOptions = [
  { value: 0, label: 'Channel A' },
  { value: 1, label: 'Channel B' },
  { value: 2, label: 'Channel C' },
  { value: 3, label: 'Channel D' },
];

const channelColours = {
    'Channel A': 'rgb(0, 110, 255)',
    'Channel B': 'rgb(255, 17, 0)',
    'Channel C': 'rgb(83, 181, 13)',
    'Channel D': 'rgb(255, 230, 0)',
};

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

const LiveView = ({ pico_endpoint, EndpointCheckbox, canRun }) => {
    const [isPlaying, setIsPlaying] = useState(true);
    const [lvData, setLvData] = useState(undefined);
    const [deviceSettings, setDeviceSettings] = useState(undefined);
    const [lvActiveChannels, setLvActiveChannels] = useState(undefined);
    const [preTrigSamples, setPreTrigSamples] = useState(0);
    const [postTrigSamples, setPostTrigSamples] = useState(0);

    const toggle_play = () => setIsPlaying(prev => !prev);

    useEffect(() => {
        if (isPlaying) {
            const data = pico_endpoint?.data?.device?.live_view?.lv_data;
            const settings = pico_endpoint?.data?.device?.settings;
            const activeChannels = pico_endpoint?.data?.device?.live_view?.lv_active_channels;
            const pre = -Math.abs(settings?.capture?.pre_trig_samples ?? 0);
            const post = Math.abs(settings?.capture?.post_trig_samples ?? 0);

            setLvData(data);
            setDeviceSettings(settings);
            setLvActiveChannels(activeChannels);
            setPreTrigSamples(pre);
            setPostTrigSamples(post);
        }
    }, [isPlaying, pico_endpoint.updateFlag]);

    if (lvData === undefined) {
        return <div>Loading live data...</div>;
    }

    const series_names = lvActiveChannels.map(ch => {
        const found = sourceOptions.find(opt => opt.value === ch);
        return found ? found.label : `Channel ${ch}`;
    });

    const prepared_data = lvData.slice(0, lvActiveChannels.length).map((y_array, idx) => {
        const x_array = generateXValues(preTrigSamples, y_array);
        const channel_name = series_names[idx] || `Channel ${idx}`;
        const trace = {
            x: x_array,
            y: y_array,
            name: channel_name,
            line: { color: channelColours[channel_name] },
        };

        if (lvActiveChannels.length === 2 && idx === 1) {
            trace.yaxis = 'y2';
        }

        return trace;
    });

    const getChannelRange = (deviceSettings, lvActiveChannels, index) => {
        if (!deviceSettings || !lvActiveChannels || lvActiveChannels.length <= index) {
            return [0, 0];
        }
        const ch_id = lvActiveChannels[index];
        const ch_key = channelIdToKey[ch_id];
        const ch_range = deviceSettings.channels?.[ch_key]?.range;
        const yrange = rangeValueToMilliVolts[ch_range] ?? 1000;
        return [-yrange, yrange];
    };

    let maxRange = 0;
    if (lvActiveChannels.length >= 3) {
        maxRange = Math.max(...lvActiveChannels.map((ch_id) => {
            const ch_key = channelIdToKey[ch_id];
            const ch_range = deviceSettings.channels?.[ch_key]?.range;
            return rangeValueToMilliVolts[ch_range] ?? 1000;
        }));
    }

    const layout = {
        uirevision: 'true',
        showlegend: lvActiveChannels.length === 0 ? false : true,
        xaxis: {
            title: { text: 'Sample Interval' },
            range: [preTrigSamples, postTrigSamples]
        },
        yaxis: {
            nticks: 15,
            //tickformat: '.1f',
            title: lvActiveChannels.length >= 3
                ? { text: "Channel Voltage (mV)" }
                : { text: (prepared_data[0]?.name+" Voltage (mV)")},
            range: lvActiveChannels.length >= 3
                ? [-maxRange, maxRange]
                : getChannelRange(deviceSettings, lvActiveChannels, 0)
        },
        yaxis2: {
            title: { text: (prepared_data[1]?.name+" Voltage (mV)")},
            overlaying: 'y',
            side: 'right',
            visible: lvData.length === 2,
            range: getChannelRange(deviceSettings, lvActiveChannels, 1),
            nticks: 15,
            //tickformat: '.1f',
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
            <UICard
                headerContent={
                    <>
                        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet"></link>
                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                            Live View
                            <div>
                                <span style={{ marginRight: '18px', marginLeft: '80px' }}>Channels:</span>
                                {channels.map((ch) => (
                                    <React.Fragment key={ch}>
                                        <EndpointCheckbox
                                            id={`channel-${ch}-liveview`}
                                            endpoint={pico_endpoint}
                                            fullpath={`device/settings/channels/${ch}/live_view`}
                                            disabled={!canRun[ch]}
                                        />
                                        <span style={{ margin: '0 8px' }}>{ch.toUpperCase()}</span>
                                    </React.Fragment>
                                ))}
                            </div>

                            <button
                                id="p_p_button_lv"
                                className="icon-button"
                                onClick={toggle_play}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    marginLeft: 'auto',
                                }}
                            >
                                <span className="material-icons">{isPlaying ? 'pause_circle_outline' : 'play_circle_outline'}</span>
                            </button>
                        </div>
                    </>
                }
            >
            <OdinGraph
                data={prepared_data}
                layout={layout}
                style={{ height: '300px' }}
            />
            </UICard>
        </>
    )
}


export default LiveView
import { OdinGraph } from 'odin-react';
import React, {useState, useEffect} from 'react';

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

const CurrentPHA = ({ pico_endpoint, EndpointCheckbox, canRun }) => {
    const [isPlaying, setIsPlaying] = useState(true);
    const [phaCounts, setPhaCounts] = useState(undefined);
    const [deviceSettings, setDeviceSettings] = useState(undefined);
    const [phaActiveChannels, setPhaActiveChannels] = useState(undefined);
    const [lowerRange, setLowerRange] = useState(0);
    const [upperRange, setUpperRange] = useState(0);
    const [binEdges, setBinEdges] = useState([]);

    const toggle_play = () => setIsPlaying(prev => !prev);

    useEffect(() => {
        if (isPlaying) {
            const data = pico_endpoint?.data?.device?.live_view?.pha_counts;
            const settings = pico_endpoint?.data?.device?.settings;
            const activeChannels = pico_endpoint?.data?.device?.live_view?.pha_active_channels;
            const low = pico_endpoint?.data?.device?.settings?.pha?.lower_range;
            const up = pico_endpoint?.data?.device?.settings?.pha?.upper_range;
            const edges = pico_endpoint?.data?.device?.live_view?.pha_bin_edges;

            setPhaCounts(data);
            setDeviceSettings(settings);
            setPhaActiveChannels(activeChannels);
            setLowerRange(low);
            setUpperRange(up);
            setBinEdges(edges);
        }
    }, [isPlaying, pico_endpoint.updateFlag]);

    if (phaCounts === undefined) {
        return <div>Loading live data...</div>;
    }

    const prepared_data = phaActiveChannels.map((channel_idx) => {
        const y_array = phaCounts[channel_idx];
        const x_array = binEdges;
        const found = sourceOptions.find(opt => opt.value === channel_idx);
        const channel_name = found ? found.label : `Channel ${channel_idx}`;

        const trace = {
            x: x_array,
            y: y_array,
            name: channel_name,
            line: { color: channelColours[channel_name] },
        };

        return trace;
    });

    const layout = {
        uirevision: 'true',
        showlegend: phaActiveChannels.length === 0 ? false : true,
        xaxis: {
            title: { text: 'Energy Level' },
            range: [lowerRange, upperRange]
        },
        yaxis: {
            title: { text: "Counts" },
        },
        title: {
            text: 'Current PHA Data'
        },
        margin: {
            t: 40,
            b: 40,
            l: 50,
            r: 50
        },
    };

    if (prepared_data.length === 0) {
        prepared_data.push(0);
    }

    const handleClearPHA = () => {
        pico_endpoint.put(true, 'device/commands/clear_pha');
    };

    const channels = ['a', 'b', 'c', 'd'];

    return (
        <>
            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet"></link>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <div>
                    <span style={{ marginRight: '8px' }}>Select Channels to preview PHA:</span>
                    {channels.map((ch) => (
                        <React.Fragment key={ch}>
                            <EndpointCheckbox
                                id={`channel-${ch}-pha`}
                                endpoint={pico_endpoint}
                                fullpath={`device/settings/channels/${ch}/pha_active`}
                                disabled={!canRun[ch]}
                            />
                            <span style={{ margin: '0 8px' }}>{ch.toUpperCase()}</span>
                        </React.Fragment>
                    ))}
                </div>

                <div style={{ marginLeft: 'auto', marginRight: 'auto', textAlign: 'center' }}>
                    <span>Clear PHA Data</span>
                    <button
                        type="button"
                        id="clear_pha_btn"
                        onClick={handleClearPHA}
                        style={{
                            marginLeft: '8px',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Clear
                    </button>
                </div>

                <button
                    id="p_p_button_pha"
                    className="icon-button"
                    onClick={toggle_play}
                    style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        marginLeft: 'auto',
                        paddingRight: '150px',
                    }}
                >
                    <span className="material-icons">{isPlaying ? 'pause_circle_outline' : 'play_circle_outline'}</span>
                </button>
            </div>

            <OdinGraph
                data={prepared_data}
                layout={layout}
                style={{ height: '300px' }}
            />
        </>
    )
}
export default CurrentPHA

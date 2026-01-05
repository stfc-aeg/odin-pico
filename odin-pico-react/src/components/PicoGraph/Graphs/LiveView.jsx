import { OdinGraph } from 'odin-react';
import { useState, useEffect } from 'react';
import { Card, Button } from 'react-bootstrap';

import 'bootstrap-icons/font/bootstrap-icons.css';

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

const channelIdToKey = { 0: 'a', 1: 'b', 2: 'c', 3: 'd' };
const rangeValueToMilliVolts = {
  '0': 10, '1': 20, '2': 50, '3': 100, '4': 200, '5': 500,
  '6': 1000, '7': 2000, '8': 5000, '9': 10000, '10': 20000,
};

const generateXValues = (start_x, y_array, step = 1) =>
  Array.isArray(y_array) ? Array.from({ length: y_array.length }, (_, i) => start_x + i * step) : [];

const LiveView = ({ pico_endpoint, EndpointCheckbox, canRun }) => {
  const [isPlaying, setIsPlaying] = useState(true);
  const [lvData, setLvData] = useState(undefined);
  const [deviceSettings, setDeviceSettings] = useState(undefined);
  const [lvActiveChannels, setLvActiveChannels] = useState(undefined);
  const [preTrigSamples, setPreTrigSamples] = useState(0);
  const [postTrigSamples, setPostTrigSamples] = useState(0);

  const toggle_play = () => setIsPlaying(prev => !prev);

  useEffect(() => {
    if (!isPlaying) return;

    const data = pico_endpoint?.data?.device?.live_view?.lv_data;
    const settings = pico_endpoint?.data?.device?.settings;
    const activeChannels = pico_endpoint?.data?.device?.live_view?.lv_active_channels;
    const pre = -Math.abs(settings?.capture?.pre_trig_samples ?? 0);
    const post = Math.abs(settings?.capture?.post_trig_samples ?? 0);

    setLvData(Array.isArray(data) ? data : []);
    setDeviceSettings(settings ?? {});
    setLvActiveChannels(Array.isArray(activeChannels) ? activeChannels : []);
    setPreTrigSamples(Number.isFinite(pre) ? pre : 0);
    setPostTrigSamples(Number.isFinite(post) ? post : 0);
  }, [isPlaying, pico_endpoint.updateFlag]);

  if (!Array.isArray(lvData)) return <div>Loading live data...</div>;

  const getChannelLabel = (id) => {
    const found = sourceOptions.find(opt => opt.value === id);
    return found ? found.label : `Channel ${id}`;
  };

  const getChannelRange = (settings, active, index) => {
    if (!settings || !Array.isArray(active) || active.length <= index) return [0, 0];
    const ch_id = active[index];
    const ch_key = channelIdToKey[ch_id];
    const ch_range = settings?.channels?.[ch_key]?.range;
    const yrange = rangeValueToMilliVolts[ch_range] ?? 1000;
    return [-yrange, yrange];
  };

  const safeActive = Array.isArray(lvActiveChannels) ? lvActiveChannels : [];
  const series_names = safeActive.map(getChannelLabel);

  const prepared_data = safeActive.map((chId, idx) => {
    const y_array = Array.isArray(lvData[idx]) ? lvData[idx] : null;
    if (!y_array) return null;

    const x_array = generateXValues(preTrigSamples, y_array);
    if (!x_array.length || !y_array.length) return null;

    const name = series_names[idx] || `Channel ${idx}`;
    const trace = {
      x: x_array,
      y: y_array,
      name,
      mode: 'lines',
      line: { color: channelColours[name] },
    };

    if (safeActive.length === 2 && idx === 1) trace.yaxis = 'y2';
    return trace;
  }).filter(Boolean);

  let maxRange = 0;
  if (safeActive.length >= 3 && deviceSettings?.channels) {
    maxRange = Math.max(
      ...safeActive.map((ch_id) => {
        const ch_key = channelIdToKey[ch_id];
        const code = deviceSettings.channels?.[ch_key]?.range;
        return rangeValueToMilliVolts[code] ?? 1000;
      })
    );
  }

  // Always pass a valid array to OdinGraph
  const graphData = prepared_data.length
    ? prepared_data
    : [{ x: [], y: [], name: 'No data', mode: 'lines' }];

  const layout = {
    uirevision: 'true',
    showlegend: prepared_data.length > 0,
    xaxis: {
      title: { text: 'Sample Interval' },
      range: [preTrigSamples, postTrigSamples],
    },
    yaxis: {
      nticks: 15,
      title:
        safeActive.length >= 3
          ? { text: 'Channel Voltage (mV)' }
          : { text: `${prepared_data[0]?.name ?? 'Channel'} Voltage (mV)` },
      range:
        safeActive.length >= 3
          ? [-maxRange, maxRange]
          : getChannelRange(deviceSettings, safeActive, 0),
    },
    yaxis2: {
      title: { text: `${prepared_data[1]?.name ?? ''} Voltage (mV)` },
      overlaying: 'y',
      side: 'right',
      visible: prepared_data.length === 2,
      range: getChannelRange(deviceSettings, safeActive, 1),
      nticks: 15,
    },
    margin: { t: 40, b: 40, l: 50, r: 50 },
    legend: { orientation: 'h', y: -0.2, x: 0, xanchor: 'left' },
  };

  const channels = ['a', 'b', 'c', 'd'];
  const handleTogglePlay = () => setIsPlaying(p => !p);

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        <>
          <div className="d-flex align-items-center">
            <div className="d-flex align-items-center">
              <span>Live View</span>
              <div className="d-flex align-items-center ms-5">
                <span className="me-3">Channels:</span>
                {channels.map((ch) => (
                  <span key={ch} className="d-inline-flex align-items-center me-3">
                    <EndpointCheckbox
                      id={`channel-${ch}-liveview`}
                      endpoint={pico_endpoint}
                      fullpath={`device/settings/channels/${ch}/live_view`}
                      disabled={!canRun[ch]}
                    />
                    <span className="ms-1">{ch.toUpperCase()}</span>
                  </span>
                ))}
              </div>
            </div>

            <Button
              id="p_p_button_live"
              variant="link"
              className="ms-auto p-0"
              onClick={handleTogglePlay}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              <span className={`bi ${isPlaying ? 'bi-pause-circle' : 'bi-play-circle'} icons`} />
            </Button>
          </div>
        </>
      </Card.Header>

      <Card.Body className="p-0">
        <OdinGraph data={graphData} layout={layout} style={{ height: '300px' }} />
      </Card.Body>
    </Card>
  );
};

export default LiveView;

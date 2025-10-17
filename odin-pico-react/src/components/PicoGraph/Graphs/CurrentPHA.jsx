import { OdinGraph } from 'odin-react';
import { useState, useEffect } from 'react';
import { Card, Button } from 'react-bootstrap';

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
  const [phaActiveChannels, setPhaActiveChannels] = useState(undefined);
  const [lowerRange, setLowerRange] = useState(0);
  const [upperRange, setUpperRange] = useState(0);
  const [binEdges, setBinEdges] = useState([]);

  const toggle_play = () => setIsPlaying(prev => !prev);

  useEffect(() => {
    if (!isPlaying) return;

    const data = pico_endpoint?.data?.device?.live_view?.pha_counts;
    const activeChannels = pico_endpoint?.data?.device?.live_view?.pha_active_channels;
    const low = pico_endpoint?.data?.device?.settings?.pha?.lower_range;
    const up = pico_endpoint?.data?.device?.settings?.pha?.upper_range;
    const edges = pico_endpoint?.data?.device?.live_view?.pha_bin_edges;

    setPhaCounts(data);
    setPhaActiveChannels(activeChannels);
    setLowerRange(Number.isFinite(low) ? low : 0);
    setUpperRange(Number.isFinite(up) ? up : 0);
    setBinEdges(Array.isArray(edges) ? edges : []);
  }, [isPlaying, pico_endpoint.updateFlag]);

  if (!phaCounts) {
    return <div>Loading live data...</div>;
  }

  const channels = ['a', 'b', 'c', 'd'];

  const safeActive = Array.isArray(phaActiveChannels) ? phaActiveChannels : [];
  const prepared_data = safeActive
    .map((channel_idx) => {
      const y_array = Array.isArray(phaCounts[channel_idx]) ? phaCounts[channel_idx] : null;
      const x_array = Array.isArray(binEdges) ? binEdges : null;
      if (!y_array || !x_array) return null;

      const found = sourceOptions.find(opt => opt.value === channel_idx);
      const channel_name = found ? found.label : `Channel ${channel_idx}`;
      return {
        x: x_array,
        y: y_array,
        name: channel_name,
        mode: 'lines',
        line: { color: channelColours[channel_name] || undefined },
      };
    })
    .filter(Boolean);

  // Ensure OdinGraph always receives a valid array for data
  const graphData = prepared_data.length
    ? prepared_data
    : [{ x: [], y: [], name: 'No data', mode: 'lines' }];

  const layout = {
    uirevision: 'true',
    showlegend: prepared_data.length > 0,
    xaxis: { title: { text: 'Energy Level' }, range: [lowerRange, upperRange] },
    yaxis: { title: { text: 'Counts' } },
    margin: { t: 40, b: 40, l: 50, r: 50 },
  };

  const handleClearPHA = () => {
    pico_endpoint.put(true, 'device/commands/clear_pha');
  };

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        <>
          <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" />
          <div className="d-flex align-items-center">
            <div className="d-flex align-items-center">
              <span>PHA</span>

              <div className="d-flex align-items-center ms-5">
                <span className="me-3">Channels:</span>
                {channels.map((ch) => (
                  <span key={ch} className="d-inline-flex align-items-center me-3">
                    <EndpointCheckbox
                      id={`channel-${ch}-pha`}
                      endpoint={pico_endpoint}
                      fullpath={`device/settings/channels/${ch}/pha_active`}
                      disabled={!canRun[ch]}
                    />
                    <span className="ms-1">{ch.toUpperCase()}</span>
                  </span>
                ))}
              </div>
            </div>

            <div className="mx-auto">
              <Button id="clear_pha_btn" size="sm" variant="primary" onClick={handleClearPHA}>
                Clear Data
              </Button>
            </div>

            <Button
              id="p_p_button_pha"
              variant="link"
              className="ms-auto p-0"
              onClick={toggle_play}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              <span className="material-icons">
                {isPlaying ? 'pause_circle_outline' : 'play_circle_outline'}
              </span>
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

export default CurrentPHA;

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
    return {
      x: x_array,
      y: y_array,
      name: channel_name,
      line: { color: channelColours[channel_name] },
    };
  });

  const layout = {
    uirevision: 'true',
    showlegend: phaActiveChannels.length === 0 ? false : true,
    xaxis: { title: { text: 'Energy Level' }, range: [lowerRange, upperRange] },
    yaxis: { title: { text: 'Counts' } },
    margin: { t: 40, b: 40, l: 50, r: 50 },
  };

  const handleClearPHA = () => {
    pico_endpoint.put(true, 'device/commands/clear_pha');
  };

  const channels = ['a', 'b', 'c', 'd'];

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom"
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
              <Button
                id="clear_pha_btn"
                size="sm"
                variant="primary"
                onClick={handleClearPHA}
              >
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
        <OdinGraph data={prepared_data} layout={layout} style={{ height: '300px' }} />
      </Card.Body>
    </Card>
  );
};

export default CurrentPHA;
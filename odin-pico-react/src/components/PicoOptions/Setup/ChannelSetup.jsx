import { Row, Col, InputGroup, Card } from 'react-bootstrap';
import { getChannelRowClass } from '../../utils/utils';

const couplingOptions = [
  { value: '1', label: 'DC' },
  { value: '0', label: 'AC' },
];

const rangeOptions = [
  { value: '0', label: '10 mV' },
  { value: '1', label: '20 mV' },
  { value: '2', label: '50 mV' },
  { value: '3', label: '100 mV' },
  { value: '4', label: '200 mV' },
  { value: '5', label: '500 mV' },
  { value: '6', label: '1 V' },
  { value: '7', label: '2 V' },
  { value: '8', label: '5 V' },
  { value: '9', label: '10 V' },
  { value: '10', label: '20 V' },
];

const ChannelSetup = ({
  anyActive,
  pico_endpoint,
  EndpointInput,
  EndpointSelect,
  EndpointToggleSwitch,
  captureRunning
}) => {
  const channelObj = pico_endpoint?.data?.device?.settings?.channels ?? {};
  const channelStates = Object.entries(channelObj).map(([id, data]) => ({
    id,
    label: id.toUpperCase(),
    active: data.active,
    coupling: String(data.coupling),
    range: String(data.range),
    offset: String(data.offset),
  }));

  const activeChannels = channelStates.filter(ch => ch.active);
  const allOffsetsInvalid =
    activeChannels.length > 0 &&
    activeChannels.every(ch => Number(ch.offset) > 100 || Number(ch.offset) < -100);

  const headerRowClass = allOffsetsInvalid ? 'bg-red' : getChannelRowClass(true, anyActive, true);

  return (
      <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Title
        className="px-3 py-2 border-bottom m-0 fw-semibold"
        style={{ 
          fontSize: '0.85rem', 
          backgroundColor: '#f5f5f5' 
        }}
        >Channel Setup
        </Card.Title>
        <Row className={headerRowClass} id="chan-row" style={{ margin: 0, padding: '0.5rem 0' }}>
          <Col md={2} className="text-center"><label>Enable</label></Col>
          <Col md={2} className="align-top"><label>Coupling</label></Col>
          <Col md={2} className="align-top"><label>Range</label></Col>
          <Col md={2} className="align-top"><label>Offset (%)</label></Col>
          <Col md={4} className="text-center"><label>Output</label></Col>
        </Row>
        {channelStates.map(({ id, label, active, coupling, range, offset }) => {
          const rowClass =
            Number(offset) > 100 || Number(offset) < -100
              ? 'bg-red'
              : getChannelRowClass(active, anyActive, true);

          return (
            <Row key={id} id={`channel-${id}-set`} className={rowClass}>
              <Col md={2} className="d-flex justify-content-center align-items-center py-2">
                <div 
                  className="d-flex align-items-center justify-content-center gap-2"
                  style={{ minWidth: 'fit-content' }}
                >
                  <label className="mb-0 text-nowrap text-center" style={{ minWidth: '60px' }}>
                    {label}
                  </label>
                  <EndpointToggleSwitch
                    id={`channel-${id}-active`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/active`}
                    disabled={captureRunning}
                  />
                </div>
              </Col>
              <Col md={2} className="py-2">
                <InputGroup size="sm" className="mb-2">
                  <EndpointSelect
                    id={`channel-${id}-coupl`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/coupling`}
                    disabled={captureRunning}
                  >
                    {couplingOptions.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </EndpointSelect>
                </InputGroup>
              </Col>
              <Col md={2} className="py-2">
                <InputGroup size="sm" className="mb-2">
                  <EndpointSelect
                    id={`channel-${id}-range`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/range`}
                    disabled={captureRunning}
                  >
                    {rangeOptions.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </EndpointSelect>
                </InputGroup>
              </Col>
              <Col md={2} className="py-2">
                <InputGroup size="sm" className="mb-2">
                  <EndpointInput
                    id={`channel-${id}-offset`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/offset`}
                    type="number"
                    disabled={captureRunning}
                  />
                </InputGroup>
              </Col>
              <Col md={4} className="py-2">
                <Row>
                  <Col md={7} className="d-flex justify-content-center align-items-center gap-2">
                    <label className="mb-0 text-center">Waveform</label>
                    <EndpointToggleSwitch
                      id={`channel-${id}-waveform`}
                      endpoint={pico_endpoint}
                      fullpath={`device/settings/channels/${id}/waveformsToggled`}
                      disabled={captureRunning}
                    />
                  </Col>
                  <Col md={5} className="d-flex justify-content-center align-items-center gap-2">
                    <label className="mb-0 text-center">PHA</label>
                    <EndpointToggleSwitch
                      id={`channel-${id}-pha`}
                      endpoint={pico_endpoint}
                      fullpath={`device/settings/channels/${id}/PHAToggled`}
                      disabled={captureRunning}
                    />
                  </Col>
                </Row>
              </Col>
            </Row>
          );
        })}
      </Card>
  );
};

export default ChannelSetup;

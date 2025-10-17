import Card from 'react-bootstrap/Card';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';
import { Container, Row, Col, InputGroup } from 'react-bootstrap';

const sourceOptions = [
  { value: 0, label: 'Channel A' },
  { value: 1, label: 'Channel B' },
  { value: 2, label: 'Channel C' },
  { value: 3, label: 'Channel D' },
];

const directionOptions = [
  { value: 0, label: 'Above' },
  { value: 1, label: 'Below' },
  { value: 2, label: 'Rising Edge' },
  { value: 3, label: 'Falling Edge' },
  { value: 4, label: 'Rising/Falling' },
];

const rangeCodeToMillivolts = {
  0: 10, 1: 20, 2: 50, 3: 100, 4: 200, 5: 500,
  6: 1000, 7: 2000, 8: 5000, 9: 10000, 10: 20000,
};

const TriggerSetup = ({ pico_endpoint, EndpointInput, EndpointSelect, captureRunning }) => {
  const getTriggerClass = () => {
    const triggerActive = pico_endpoint?.data?.device?.settings?.trigger?.active;
    if (!triggerActive) return 'bg-grey';
    const verificationPath = pico_endpoint?.data?.device?.status?.channel_trigger_verify;
    const isValid = verificationPath === undefined ? false : verificationPath === 0;
    const currentChannelIndex = pico_endpoint?.data?.device?.settings?.trigger?.source;
    const channelLetter = ['a', 'b', 'c', 'd'][currentChannelIndex];
    const channelData = pico_endpoint?.data?.device?.settings?.channels?.[channelLetter];
    const triggerThreshold = pico_endpoint?.data?.device?.settings?.trigger?.threshold;
    if (!channelData?.active) return 'bg-red';
    const channelRangeCode = channelData?.range;
    const channelRange = rangeCodeToMillivolts[channelRangeCode];
    if (isValid && triggerThreshold <= channelRange) return 'bg-green';
    return 'bg-red';
  };

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Trigger Setup
      </Card.Header>

      <div className="p-0">
        <Container fluid className="p-0">
          <div className={`${getTriggerClass()} p-1`}>
            <Row className="g-3 align-items-center">
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Mode</InputGroup.Text>
                  <ButtonGroup size="sm" className="flex-grow-1">
                    {[
                      { name: 'Free Running', value: false },
                      { name: 'Triggered', value: true },
                    ].map((opt, idx) => (
                      <ToggleButton
                        key={idx}
                        type="radio"
                        variant="outline-primary"
                        name="trigger-mode"
                        value={opt.value.toString()}
                        checked={
                          (pico_endpoint?.data?.device?.settings?.trigger?.active ?? 0) === opt.value
                        }
                        onClick={() =>
                          pico_endpoint.put(opt.value, 'device/settings/trigger/active')
                        }
                        disabled={captureRunning}
                        className={
                          (pico_endpoint?.data?.device?.settings?.trigger?.active ?? 0) !==
                          opt.value
                            ? 'bg-white'
                            : ''
                        }
                      >
                        {opt.name}
                      </ToggleButton>
                    ))}
                  </ButtonGroup>
                </InputGroup>
              </Col>
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Source</InputGroup.Text>
                  <EndpointSelect
                    endpoint={pico_endpoint}
                    fullpath="device/settings/trigger/source"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  >
                    {sourceOptions.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </EndpointSelect>
                </InputGroup>
              </Col>
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Direction</InputGroup.Text>
                  <EndpointSelect
                    endpoint={pico_endpoint}
                    fullpath="device/settings/trigger/direction"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  >
                    {directionOptions.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </EndpointSelect>
                </InputGroup>
              </Col>
            </Row>
            <Row className="g-3 align-items-center mt-2">
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Threshold (mV)</InputGroup.Text>
                  <EndpointInput
                    endpoint={pico_endpoint}
                    fullpath="device/settings/trigger/threshold"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                </InputGroup>
              </Col>
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Delay (ms)</InputGroup.Text>
                  <EndpointInput
                    endpoint={pico_endpoint}
                    fullpath="device/settings/trigger/delay"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                </InputGroup>
              </Col>
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Auto (ms)</InputGroup.Text>
                  <EndpointInput
                    endpoint={pico_endpoint}
                    fullpath="device/settings/trigger/auto_trigger"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                </InputGroup>
              </Col>
            </Row>

          </div>
        </Container>
      </div>
    </Card>

  );
};

export default TriggerSetup;

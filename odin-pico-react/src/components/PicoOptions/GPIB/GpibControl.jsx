import { Card, Container, Row, Col, ButtonGroup, ToggleButton, InputGroup } from 'react-bootstrap';

const GpibControl = ({ pico_endpoint, EndpointSelect, EndpointToggleSwitch, captureRunning }) => {
  const availableTecs = pico_endpoint?.data?.gpib?.available_tecs ?? [];

  const tempActive = pico_endpoint?.data?.gpib?.temp_sweep?.active;
  const cardActive = tempActive ? 'Temperature Sweep' : 'Single Shot';
  const cardToggleRadios = [
    { name: 'Single Shot', value: 'Single Shot' },
    { name: 'Temperature Sweep', value: 'Temperature Sweep' },
  ];

  const handleRadioValueChange = (newValue, comp, path) => {
    const capMode = newValue === comp;
    pico_endpoint.put(!capMode, path);
  };

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Control
      </Card.Header>

      <Card.Body className="p-2">
        <Container fluid>
          <Row className="g-3 align-items-center">
            <Col md={5}>
              <InputGroup size="sm" className="w-100">
                <InputGroup.Text>Mode</InputGroup.Text>
                <ButtonGroup size="sm" className="flex-grow-1">
                  {cardToggleRadios.map((radio, idx) => (
                    <ToggleButton
                      key={idx}
                      type="radio"
                      variant="outline-primary"
                      name="cardToggleRadio"
                      value={radio.value}
                      checked={cardActive === radio.value}
                      onClick={() =>
                        handleRadioValueChange(radio.value, 'Single Shot', 'gpib/temp_sweep/active')
                      }
                      disabled={captureRunning}
                      className={cardActive !== radio.value ? 'bg-white' : ''}
                    >
                      {radio.name}
                    </ToggleButton>
                  ))}
                </ButtonGroup>
              </InputGroup>
            </Col>

            <Col md={3}>
              <InputGroup size="sm" className="w-100">
                <InputGroup.Text>Device</InputGroup.Text>
                <EndpointSelect
                  id="gpib-device"
                  endpoint={pico_endpoint}
                  fullpath="gpib/selected_tec"
                  type="number"
                  disabled={captureRunning}
                  className="flex-grow-1"
                >
                  {availableTecs.map((tec, idx) => (
                    <option key={idx} value={tec}>
                      {tec}
                    </option>
                  ))}
                </EndpointSelect>
              </InputGroup>
            </Col>

            <Col md={2} className="d-flex align-items-center justify-content-center gap-2">
              <span>Enable</span>
              <EndpointToggleSwitch
                endpoint={pico_endpoint}
                fullpath="gpib/gpib_control"
                disabled={captureRunning}
              />
            </Col>

            <Col md={2} className="d-flex align-items-center justify-content-center gap-2">
              <span>Output</span>
              <EndpointToggleSwitch
                endpoint={pico_endpoint}
                fullpath="gpib/output_state"
                disabled={captureRunning}
              />
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default GpibControl;

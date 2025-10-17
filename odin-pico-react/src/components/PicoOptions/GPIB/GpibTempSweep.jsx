import { Card, Container, Row, Col, InputGroup } from 'react-bootstrap';

const GpibTempSweep = ({ pico_endpoint, EndpointInput, captureRunning }) => {
  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Temperature Sweep
      </Card.Header>

      <Card.Body className="p-0">
        <Container fluid className="px-3 py-3">
          <Row className="g-3 align-items-center">
            <Col md={6}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Start °C</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="gpib/temp_sweep/t_start"
                  type="number"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>

            <Col md={6}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>End °C</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="gpib/temp_sweep/t_end"
                  type="number"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>
          </Row>

          <Row className="g-3 align-items-center">
            <Col md={6}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Step °C</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="gpib/temp_sweep/t_step"
                  type="number"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>

            <Col md={6}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Tolerance °C</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="gpib/temp_sweep/tol"
                  type="number"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default GpibTempSweep;

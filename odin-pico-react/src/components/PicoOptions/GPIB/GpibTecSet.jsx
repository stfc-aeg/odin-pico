import { Card, Container, Row, Col, InputGroup, Button } from 'react-bootstrap';

const GpibTecSet = ({ pico_endpoint, EndpointInput, captureRunning }) => {
  const handleButtonClick = (path) => {
    pico_endpoint.put(true, path);
  };

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Single-Shot TEC Set
      </Card.Header>

      <Card.Body className="p-0">
        <Container fluid className="px-3 py-3">
          <Row className="g-3 align-items-center">
            <Col md={6}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Target °C</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="gpib/set/temp_target"
                  type="number"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>

            <Col
              md={6}
              className="d-flex justify-content-center align-items-center"
            >
              <Button
                variant="success"
                size="sm"
                onClick={() => handleButtonClick('gpib/set/set_temp')}
                disabled={captureRunning}
                className="w-50"
              >
                Set
              </Button>
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default GpibTecSet;

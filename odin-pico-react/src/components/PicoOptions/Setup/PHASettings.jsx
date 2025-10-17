import Card from 'react-bootstrap/Card';
import { InputGroup, Row, Col, Container } from 'react-bootstrap';

const PHASettings = ({ pico_endpoint, EndpointInput, captureRunning }) => {
  const is_pha_verified = pico_endpoint?.data?.device?.status?.capture_settings_verify;
  const bgClass = is_pha_verified === 0 ? 'bg-green' : 'bg-red';

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        PHA Settings
      </Card.Header>

      <div className="p-0">
        <Container fluid className="p-0">
          <div className={`${bgClass} p-1`}>
            <Row className="g-3 align-items-center">
              {/* Number of Bins */}
              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Bins</InputGroup.Text>
                  <EndpointInput
                    id="num_bins"
                    endpoint={pico_endpoint}
                    fullpath="device/settings/pha/num_bins"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                </InputGroup>
              </Col>

              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Lower Range</InputGroup.Text>
                  <EndpointInput
                    id="lower_range"
                    endpoint={pico_endpoint}
                    fullpath="device/settings/pha/lower_range"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                </InputGroup>
              </Col>

              <Col md={4}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Upper Range</InputGroup.Text>
                  <EndpointInput
                    id="upper_range"
                    endpoint={pico_endpoint}
                    fullpath="device/settings/pha/upper_range"
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

export default PHASettings;

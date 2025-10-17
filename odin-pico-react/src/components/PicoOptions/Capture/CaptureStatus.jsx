import { Card, Container, Row, Col } from 'react-bootstrap';
import ProgressBar from './ProgressBar';

const CaptureStatus = ({ pico_endpoint, captureRunning }) => {
  const progressClass = captureRunning ? 'bg-green' : '';
  const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};

  const file = fileSettingsPath?.curr_file_name;
  const recorded = fileSettingsPath?.last_write_success ? "True" : "False";
  const systemState = pico_endpoint?.data?.device?.flags?.system_state;

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Capture Status
      </Card.Header>

      <Card.Body className={`p-3 ${progressClass}`} style={{ fontSize: '14px' }}>
        <Container fluid>
          <Row className="mb-2">
            <Col md={6}>
              <strong>Filename:</strong><br />
              {file || '—'}
            </Col>
            <Col md={6}>
              <strong>Recorded:</strong><br />
              {recorded}
            </Col>
          </Row>

          <Row>
            <Col>
              <ProgressBar response={pico_endpoint?.data} />
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default CaptureStatus;

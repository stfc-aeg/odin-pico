import { Card, Container, Row, Col } from 'react-bootstrap';
import { toSiUnit } from '../../utils/utils';

const GpibTecStatus = ({ pico_endpoint }) => {
  const setPoint = pico_endpoint?.data?.gpib?.info?.tec_setpoint ?? 0;
  const measured = pico_endpoint?.data?.gpib?.info?.tec_temp_meas ?? 0;
  const current = pico_endpoint?.data?.gpib?.info?.tec_current ?? 0;
  const voltage = pico_endpoint?.data?.gpib?.info?.tec_voltage ?? 0;

  const format2dp = (v) => Number(v).toFixed(2);

  const formatSi2dp = (v) => {
    const s = String(toSiUnit(Number(v)));
    const m = s.match(/^(-?\d+(?:\.\d+)?)(.*)$/);
    if (!m) return s;
    const num = Number(m[1]);
    const suffix = m[2];
    return `${num.toFixed(2)}${suffix}`;
  };

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        TEC Status
      </Card.Header>

      <Card.Body className="p-0">
        <Container fluid className="px-3 py-3" style={{ fontSize: '14px' }}>
          <Row className="g-3 align-items-center text-center">
            <Col md={3}>
              <strong>Set-point:</strong> {format2dp(setPoint)}°C
            </Col>
            <Col md={3}>
              <strong>Measured:</strong> {format2dp(measured)}°C
            </Col>
            <Col md={3}>
              <strong>Current:</strong> {formatSi2dp(current)}A
            </Col>
            <Col md={3}>
              <strong>Voltage:</strong> {formatSi2dp(voltage)}V
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default GpibTecStatus;

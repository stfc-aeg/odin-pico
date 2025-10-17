import Card from 'react-bootstrap/Card';
import { getChannelRowClass, toSiUnit } from '../../utils/utils';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';
import { Container, Row, Col, InputGroup } from 'react-bootstrap';

const GeneralSetup = ({ pico_endpoint, anyActive, EndpointInput, captureRunning }) => {
  const verificationPath = pico_endpoint?.data?.device?.status;
  const hasInvalid = verificationPath === undefined ? false : verificationPath.pico_setup_verify === 0 ? true : false;

  const baseRowClass = getChannelRowClass(true, anyActive);
  const rowClass = !hasInvalid ? 'bg-red' : baseRowClass;

  const sampTime = pico_endpoint?.data?.device?.settings?.mode?.samp_time;
  const sampTimeText = sampTime === undefined ? 'Processing...' : `${toSiUnit(sampTime)}s`;

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        General Setup
      </Card.Header>

      <div className="p-0">
        <Container fluid className="p-0" id="general-setup-row">
          <div className={`${rowClass} p-1`}>
            <Row className="g-3 align-items-center">

        <Col md={3}>
          <InputGroup size="sm" className="w-100">
            <InputGroup.Text>Bit Depth</InputGroup.Text>
            <ButtonGroup size="sm" className="flex-grow-1 d-flex justify-content-start">
              {[
                { name: '8', value: 0 },
                { name: '12', value: 1 },
              ].map((radio, idx) => (
                <ToggleButton
                  key={idx}
                  type="radio"
                  variant="outline-primary"
                  name="bit-depth"
                  value={radio.value.toString()}
                  checked={pico_endpoint?.data?.device?.settings?.mode?.resolution === radio.value}
                  onClick={() =>
                    pico_endpoint.put(radio.value, 'device/settings/mode/resolution')
                  }
                  disabled={captureRunning}
                  className={
                    pico_endpoint?.data?.device?.settings?.mode?.resolution !== radio.value
                      ? 'bg-white'
                      : ''
                  }
                >
                  {radio.name}
                </ToggleButton>
              ))}
            </ButtonGroup>
          </InputGroup>
        </Col>

              <Col md={3}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Timebase</InputGroup.Text>
                  <EndpointInput
                    id="time-base-input"
                    endpoint={pico_endpoint}
                    fullpath="device/settings/mode/timebase"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                  <InputGroup.Text>{sampTimeText}</InputGroup.Text>
                </InputGroup>
              </Col>

              <Col md={3}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Pre-samples</InputGroup.Text>
                  <EndpointInput
                    id="capture-pretrig-samples"
                    endpoint={pico_endpoint}
                    fullpath="device/settings/capture/pre_trig_samples"
                    type="number"
                    disabled={captureRunning}
                    className="flex-grow-1"
                  />
                </InputGroup>
              </Col>

              <Col md={3}>
                <InputGroup size="sm" className="w-100">
                  <InputGroup.Text>Post-samples</InputGroup.Text>
                  <EndpointInput
                    id="capture-posttrig-samples"
                    endpoint={pico_endpoint}
                    fullpath="device/settings/capture/post_trig_samples"
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

export default GeneralSetup;

import { Card, Container, Row, Col, ButtonGroup, ToggleButton, InputGroup } from 'react-bootstrap';
import CaptureButton from './CaptureButton';

const CaptureSettings = ({ pico_endpoint, EndpointInput, captureRunning, EndpointToggleSwitch }) => {
  const fileValid = pico_endpoint?.data?.device?.status?.file_name_verify &&
   (pico_endpoint?.data?.device?.status?.open_unit === 0);
  const fileClass = fileValid ? 'bg-green' : 'bg-red';

  const capturePath = pico_endpoint?.data?.device?.settings?.capture ?? {};
  const captureMode = capturePath?.capture_mode;
  const acquisitionEnabled = capturePath?.capture_repeat;

  const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};
  const filename =
    (fileSettingsPath?.file_path || '') +
    (fileSettingsPath?.folder_name || '') +
    (fileSettingsPath?.file_name || '');

  const missedTriggers = pico_endpoint?.data?.device?.gpio?.missed_triggers
  const unexpectedTriggers = pico_endpoint?.data?.device?.gpio?.unexpected_triggers

  const settingsLabel = captureMode ? 'Time (s)' : 'Captures';
  const settingsPath = captureMode ? 'capture_time' : 'n_captures';
  const recMax = captureMode ? 'max_time' : 'max_captures';

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Capture Settings
      </Card.Header>
      <Card.Body className="p-0">
        <Container fluid className="px-3 py-3">
          <Row className="g-3 align-items-center">
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Mode</InputGroup.Text>
                <ButtonGroup size="sm" className="flex-grow-1">
                  {[
                    { name: 'Number', value: false },
                    { name: 'Time', value: true },
                  ].map((radio, idx) => (
                    <ToggleButton
                      key={idx}
                      type="radio"
                      variant="outline-primary"
                      name="captureModeSettingsRadio"
                      value={radio.value.toString()}
                      checked={
                        pico_endpoint?.data?.device?.settings?.capture?.capture_mode === radio.value
                      }
                      onClick={() =>
                        pico_endpoint.put(radio.value, 'device/settings/capture/capture_mode')
                      }
                      disabled={captureRunning}
                      className={
                        pico_endpoint?.data?.device?.settings?.capture?.capture_mode !== radio.value
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
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>{settingsLabel}</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath={`device/settings/capture/${settingsPath}`}
                  type="number"
                  disabled={captureRunning}
                />
                <InputGroup.Text
                  style={{
                    fontSize: '0.8rem',
                    color: '#666',
                    backgroundColor: '#f9f9f9',
                  }}
                >
                  Max: {capturePath?.[recMax] ?? ''}
                </InputGroup.Text>
              </InputGroup>
            </Col>
            <Col md={4} className="d-flex justify-content-center align-items-center">
              <CaptureButton
                pico_endpoint={pico_endpoint}
                captureRunning={captureRunning}
                fileValid={fileValid}
              />
            </Col>
          </Row>
          {pico_endpoint?.data?.device?.gpio?.enabled === true &&
            <Row className="g-3 align-items-left mt-1">
              <Col md={4}>
                <InputGroup size="sm" className="mb-2">
                  <InputGroup.Text>Ext. Trigger</InputGroup.Text>
                  <ButtonGroup size="sm" className="flex-grow-1">
                    {[
                      { name: 'Off', value: false },
                      { name: 'On', value: true}
                    ].map((radio, idx) => (
                      <ToggleButton
                        key={idx}
                        type="radio"
                        variant="outline-primary"
                        name="gpioActive"
                        value={radio.value.toString()}
                        checked={pico_endpoint?.data?.device?.gpio?.active === radio.value}
                        onClick={() =>
                          pico_endpoint.put(radio.value, 'device/gpio/active')
                        }
                        disabled={captureRunning}
                        className={
                          pico_endpoint?.data?.device?.gpio?.active !== radio.value
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
              <Col md={4}>
                <InputGroup size="sm" className="mb-2">
                  <InputGroup.Text>Triggers</InputGroup.Text>
                  <EndpointInput
                  id="gpio-capture-run"
                  endpoint={pico_endpoint}
                  fullpath="device/gpio/capture_run"
                  type="number"
                  disabled={captureRunning || !pico_endpoint?.data?.device?.gpio?.active}
                  />
                </InputGroup>
              </Col>
                <Col md={4}>
                  <div className="fw-semibold mb-2 text-center" style={{ fontSize: '12px' }}>
                    Tiggers Missed / Unexpected:
                  </div>
                  <Row style={{ fontSize: '12px' }}>
                    <Col className="text-center" style={{ wordBreak: 'break-all' }}>{missedTriggers}</Col>
                    <Col className="text-center" style={{ wordBreak: 'break-all' }}>{unexpectedTriggers}</Col>
                  </Row>
                </Col>
            </Row>
          }
          <Row className="g-3 align-items-center mt-1">
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Acquisition</InputGroup.Text>
                <ButtonGroup size="sm" className="flex-grow-1">
                  {[
                    { name: 'Single', value: false },
                    { name: 'Repeat', value: true },
                  ].map((radio, idx) => (
                    <ToggleButton
                      key={idx}
                      type="radio"
                      variant="outline-primary"
                      name="acquisitionNumberRadio"
                      value={radio.value.toString()}
                      checked={
                        pico_endpoint?.data?.device?.settings?.capture?.capture_repeat ===
                        radio.value
                      }
                      onClick={() =>
                        pico_endpoint.put(radio.value, 'device/settings/capture/capture_repeat')
                      }
                      disabled={captureRunning}
                      className={
                        pico_endpoint?.data?.device?.settings?.capture?.capture_repeat !==
                        radio.value
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
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Repeat #</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="device/settings/capture/repeat_amount"
                  type="number"
                  disabled={!acquisitionEnabled || captureRunning}
                />
              </InputGroup>
            </Col>
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Delay (s)</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="device/settings/capture/capture_delay"
                  type="number"
                  disabled={!acquisitionEnabled || captureRunning}
                />
              </InputGroup>
            </Col>
          </Row>
          <Row className={`g-3 align-items-center mt-2 ${fileClass}`}>
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>Folder</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="device/settings/file/folder_name"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>
            <Col md={4}>
              <InputGroup size="sm" className="mb-2">
                <InputGroup.Text>File</InputGroup.Text>
                <EndpointInput
                  endpoint={pico_endpoint}
                  fullpath="device/settings/file/file_name"
                  disabled={captureRunning}
                />
              </InputGroup>
            </Col>
            <Col md={4}>
              <div className="fw-semibold mb-1" style={{ fontSize: '12px' }}>
                Filename Preview:
              </div>
              <div style={{ fontSize: '12px', wordBreak: 'break-all' }}>{filename}</div>
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default CaptureSettings;

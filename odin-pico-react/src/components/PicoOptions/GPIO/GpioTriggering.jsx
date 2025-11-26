import { Card, Container, Row, Col, InputGroup } from 'react-bootstrap';

const GpioTriggering = ({pico_endpoint, gpio_endpoint, EndpointToggleSwitch, EndpointInput}) => {
    

    return (
        <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
        <Card.Header
            className="px-3 py-2 border-bottom fw-semibold"
            style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
        >
            GPIO Triggering
        </Card.Header>

        <Card.Body className={`p-3`} style={{ fontSize: '14px' }}>
            <Container fluid>
                <Row className="mb-2">
                    <Col md={6}>
                        <label>Active:</label>
                        <EndpointToggleSwitch
                        id="gpio-active"
                        endpoint={gpio_endpoint}
                        fullpath="active"
                        />
                    </Col>
                    <Col md={6}>
                        <InputGroup size="sm" className="mb-2">
                            <InputGroup.Text>Captures: </InputGroup.Text>
                            <EndpointInput
                            id="gpio-capture-run"
                            endpoint={pico_endpoint}
                            fullpath="device/gpio/capture_run"
                            type="number"
                            />
                        </InputGroup>
                    </Col>
                </Row>
            </Container>
        </Card.Body>
        </Card>
    )
}

export default GpioTriggering
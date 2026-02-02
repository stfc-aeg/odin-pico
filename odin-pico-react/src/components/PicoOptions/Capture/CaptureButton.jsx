import { InputGroup, Button } from 'react-bootstrap';

const CaptureControl = ({ pico_endpoint, captureRunning, fileValid }) => {
  const handleButtonClick = (path, value) => {
    if (pico_endpoint?.data?.device?.gpio?.active) {
      pico_endpoint.put(value, 'device/gpio/listening');
      return;
    }
    pico_endpoint.put(true, path);
  };

  return (
    <InputGroup size="sm" className="mb-2 justify-content-center">
      {!captureRunning ? (
        <Button
          variant="success"
          className="w-50"
          onClick={() => handleButtonClick('device/commands/run_user_capture', true)}
          disabled={!fileValid}
        >
          Start Capture
        </Button>
      ) : (
        <Button
          variant="danger"
          className="w-50"
          onClick={() => handleButtonClick('device/flags/abort_cap', false)}
          disabled={!fileValid}
        >
          Abort Capture
        </Button>
      )}
    </InputGroup>
  );
};

export default CaptureControl;

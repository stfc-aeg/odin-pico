import { InputGroup, Button } from 'react-bootstrap';

const CaptureControl = ({ pico_endpoint, captureRunning, fileValid }) => {
  const handleButtonClick = (path) => {
    pico_endpoint.put(true, path);
  };

  return (
    <InputGroup size="sm" className="mb-2 justify-content-center">
      {!captureRunning ? (
        <Button
          variant="success"
          className="w-50"
          onClick={() => handleButtonClick('device/commands/run_user_capture')}
          disabled={!fileValid}
        >
          Start Capture
        </Button>
      ) : (
        <Button
          variant="danger"
          className="w-50"
          onClick={() => handleButtonClick('device/flags/abort_cap')}
          disabled={!fileValid}
        >
          Abort Capture
        </Button>
      )}
    </InputGroup>
  );
};

export default CaptureControl;

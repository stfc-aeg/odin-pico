import { Badge } from 'react-bootstrap';

const InfoBar = ({ pico_endpoint }) => {
  let deviceStatus = null;
  let statusError = false;
  const deviceResponse = pico_endpoint?.data?.device;

  if (deviceResponse === undefined) {
    statusError = true;
  } else {
    // const runUserCapture = deviceResponse?.commands?.run_user_capture;
    // const captureMode = deviceResponse?.settings?.capture?.capture_mode;

    // let captureType;
    // if (runUserCapture === true && captureMode === false) {
    //   captureType = 'N Based Captures';
    // } else if (runUserCapture === true && captureMode === true) {
    //   captureType = 'Time Based Captures';
    // } else if (runUserCapture === false) {
    //   captureType = 'Live View';
    // } else {
    //   captureType = '-';
    // }

    deviceStatus = {
      open_unit: deviceResponse?.status?.open_unit,
      settings_verified: deviceResponse?.status?.settings_verified,
      system_state: deviceResponse?.flags?.system_state,
      // capture_type: captureType,
    };
  }

  // Mappings for system state colours
  const systemStateColours = {
    "Waiting for connection": "warning",
    "Time based collection": "success",
    "N capture collection": "success",
    "Collecting LV Data": "success",
    "Waiting for Trigger": "warning",
    "Waiting for TEC to stabilise": "warning",
    "Connected to PicoScope, Idle": "warning",
    "File Name Empty or Already Exists": "danger",
    "Delay Between Captures": "warning",
  };

  // Helper function to determine badge variant
  const getStatusVariant = (statusText) => {
    if (!statusText) {
      return "secondary";
    }
    
    // Check for exact matches
    if (systemStateColours[statusText]) {
      return systemStateColours[statusText];
    }
    
    // Check for messages that start with specific strings
    if (statusText.startsWith("Writing HDF5 File: Writing Captures:")) {
      return "warning";
    }
    if (statusText.startsWith("Setting TEC")) {
      return "warning";
    }
    
    // Default to yellow for any other message
    return "warning";
  };
  
  // Custom Badge for the image example
  const CustomBadge = ({ text, variant }) => (
    <Badge 
      bg={variant} 
      style={{
        borderRadius: '5px', 
        padding: '6px 16px', 
        fontSize: '14px',
        fontWeight: 'normal',
        color: 'white',
      }}
      className="me-2"
    >
      {text}
    </Badge>
  );

  return (
    <div className="d-flex align-items-center gap-2">
      {statusError ? (
        <CustomBadge text="Connection: Error" variant="danger" />
      ) : (
        <>
          <CustomBadge 
            text={deviceStatus?.open_unit === 0 ? "Scope: Connected" : "Scope: Disconnected"}
            variant={deviceStatus?.open_unit === 0 ? "success" : "danger"}
          />
          <CustomBadge
            text={deviceStatus?.settings_verified ? "Settings: Valid" : "Settings: Invalid"}
            variant={deviceStatus?.settings_verified ? "success" : "danger"}
          />
          <CustomBadge
            text={`System state: ${deviceStatus?.system_state || 'N/A'}`}
            variant={getStatusVariant(deviceStatus?.system_state)}
          />
        </>
      )}
    </div>
  );
};

export default InfoBar;
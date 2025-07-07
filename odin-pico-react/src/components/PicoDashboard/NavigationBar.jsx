import React from 'react';
import { Navbar, Container } from 'react-bootstrap';
import odinIcon from '../../assets/odin.png';
import logo from '../../assets/logo.png';

const NavigationBar = ({ pico_endpoint }) => {
  let deviceStatus = null;
  let statusError = false;
  const deviceResponse = pico_endpoint?.data?.device;

  if (deviceResponse === undefined) {
    statusError = true;
  } else {
    const runUserCapture = deviceResponse?.commands?.run_user_capture;
    const captureMode = deviceResponse?.settings?.capture?.capture_mode?.value;

    let captureType;
    if (runUserCapture === true && captureMode === false) {
      captureType = 'N Based Captures';
    } else if (runUserCapture === true && captureMode === true) {
      captureType = 'Time Based Captures';
    } else if (runUserCapture === false) {
      captureType = 'Live View';
    } else {
      captureType = '-';
    }

    deviceStatus ={
      open_unit: deviceResponse?.status?.open_unit,
      settings_verified: deviceResponse?.status?.settings_verified,
      system_state: deviceResponse?.flags?.system_state,
      capture_type: captureType,
    };
  }

  // Helper function to display status fields
  const renderField = (label, value) => (
    <span>
      {label}:{' '}
      <span>
        {statusError
          ? 'Error'
          : value !== undefined && value !== null
          ? value
          : '-'}
      </span>
    </span>
  );

  return (
    <Navbar
      bg="dark"
      variant="dark"
      sticky="top"
      className="navbar-inverse"
      style={{ paddingTop: 0, paddingBottom: 0 }}
    >
      <Container fluid>
        <div
          className="navbar-header d-flex align-items-center gap-3"
          style={{ height: '50px', color: 'white' }}
        >
          <div>
            <img
              src={odinIcon}
              alt="Odin Icon"
              style={{ filter: 'drop-shadow(0px 0px 30px white)' }}
            />
          </div>
          <div>
            <img
              src={logo}
              alt="Logo"
              style={{ width: '120px' }}
            />
          </div>

          <span>Status:</span>
          {renderField(
            'Connection',
            deviceStatus?.open_unit === 0 ? 'True' : deviceStatus?.open_unit === 1 ? 'False' : null
          )}
          {renderField('Capture Type', deviceStatus?.capture_type)}
          {renderField(
            'Settings valid',
            deviceStatus?.settings_verified === true
              ? 'True'
              : deviceStatus?.settings_verified === false
              ? 'False'
              : null
          )}
          {renderField('System State', deviceStatus?.system_state)}
        </div>
      </Container>
    </Navbar>
  );
};

export default NavigationBar;

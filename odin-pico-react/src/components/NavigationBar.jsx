import { Navbar, Container } from 'react-bootstrap';
import odinIcon from '../assets/odin.png';
import logo from '../assets/logo.png';
//import './NavigationBar.css';

const NavigationBar = () => {
  return (
    <Navbar
      id="custom-navbar"
      bg="dark"
      variant="dark"
      sticky="top"
      className="navbar-inverse"
    >
      <Container fluid id="custom-container-fluid">
        <div
          id="custom-navbar-header"
          className="navbar-header d-flex align-items-center gap-3"
          style={{ height: '50px' }}
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

          {/* Status Labels (TODO: make dynamic) */}
          <span style={{ color: 'white' }} id="custom-item-label">
            Status:
          </span>
          <span style={{ color: 'white' }} id="custom-item1">
            Connection: <span id="connection_status">True</span>
          </span>
          <span style={{ color: 'white' }} id="custom-item2">
            Capture Type: <span id="cap_type_status">True</span>
          </span>
          <span style={{ color: 'white' }} id="custom-item3">
            Settings valid: <span id="settings_status">True</span>
          </span>
          <span style={{ color: 'white' }} id="custom-item4">
            System State: <span id="system-state">Collecting LV Data</span>
          </span>
        </div>
      </Container>
    </Navbar>
  );
};

export default NavigationBar;

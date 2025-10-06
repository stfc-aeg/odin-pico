import React from 'react';
import { Navbar, Container, Nav } from 'react-bootstrap';
import odinIcon from '../../assets/odin.png';
import logo from '../../assets/logo.png';

const NavigationBar = ({ pico_endpoint, activeTab, setActiveTab }) => {
  const [gpibEnabled, setGpibEnabled] = React.useState(false);

  React.useEffect(() => {
    pico_endpoint.get('gpib')
      .then((response) => {
        if (response.gpib && response.gpib.gpib_avail === true) {
          setGpibEnabled(true);
        } else {
          setGpibEnabled(false);
        }
      })
      .catch(() => {
        setGpibEnabled(false);
      });
  }, []);

  return (
    <Navbar bg="dark" variant="dark" sticky="top" style={{ padding: 0 }}>
      <Container fluid>
        <Navbar.Brand>
          <div className="d-flex align-items-center gap-3">
            <img
              src={odinIcon}
              alt="Odin Icon"
              style={{ filter: 'drop-shadow(0px 0px 30px white)', height: '50px' }}
            />
            <img
              src={logo}
              alt="Logo"
              style={{ width: '120px' }}
            />
          </div>
        </Navbar.Brand>

        <Navbar.Toggle aria-controls="responsive-navbar-nav" />
        <Navbar.Collapse id="responsive-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link
              active={activeTab === 'setup'}
              onClick={() => setActiveTab('setup')}
            >
              Setup
            </Nav.Link>
            <Nav.Link
              active={activeTab === 'capture'}
              onClick={() => setActiveTab('capture')}
            >
              Capture
            </Nav.Link>
            {gpibEnabled && (
              <Nav.Link
                active={activeTab === 'gpib'}
                onClick={() => setActiveTab('gpib')}
              >
                GPIB
              </Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavigationBar;
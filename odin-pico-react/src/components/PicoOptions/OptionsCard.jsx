import React from 'react';
import ChannelSetup from './Setup/ChannelSetup';
import GeneralSetup from './Setup/GeneralSetup';
import TriggerSetup from './Setup/TriggerSetup';
import PHASettings from './Setup/PHASettings';

import CaptureSettings from './Capture/CaptureSettings';
import GpibSettings from './GPIB/GpibSettings';

import { WithEndpoint } from 'odin-react';

const EndpointInput = WithEndpoint((props) => (
  <input {...props} className={`form small-text ${props.className || ''}`} />
));

const EndpointSelect = WithEndpoint((props) => (
  <select {...props} className={`form ${props.className || ''}`}>
    {props.children}
  </select>
));

const EndpointCheckbox = WithEndpoint((props) => (
  <input type="checkbox" {...props} />
));

const OptionsCard = ({ pico_endpoint }) => {

  const [gpibEnabled, setGpibEnabled] = React.useState(false);
  const channels = pico_endpoint?.data?.device?.settings?.channels;

  let anyChannelActive;

  if (channels !== undefined) {
      anyChannelActive = Object.values(channels).some(channel => channel.active);
  } else {
      anyChannelActive = false;
  }


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
  
  const [activeTab, setActiveTab] = React.useState('setup');

  return (
    <div className="fixed-width" id="left-panel">
      <div className="tab-content p-3">
        <div className="panel-heading panel-heading-nav" style={{ backgroundColor: '#f5f5f5' }}>
          <ul className="nav nav-tabs">
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === 'setup' ? 'active' : ''}`}
                onClick={() => setActiveTab('setup')}
              >
                Setup
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${activeTab === 'capture' ? 'active' : ''}`}
                onClick={() => setActiveTab('capture')}
              >
                Capture
              </button>
            </li>
            {gpibEnabled && (
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'gpib' ? 'active' : ''}`}
                  onClick={() => setActiveTab('gpib')}
                >
                  GPIB
                </button>
              </li>
            )}
          </ul>
        </div>

        {activeTab === 'setup' && (
          <>
            <GeneralSetup
              anyActive={anyChannelActive}
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              EndpointSelect={EndpointSelect}
            />
            <ChannelSetup
              anyActive={anyChannelActive}
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              EndpointSelect={EndpointSelect}
              EndpointCheckbox={EndpointCheckbox}
            />
            <TriggerSetup
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              EndpointSelect={EndpointSelect}
            />
            <PHASettings
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
            />
          </>
        )}
        {activeTab === 'capture' && <CaptureSettings />}
        {activeTab === 'gpib' && gpibEnabled && <GpibSettings />}
      </div>
    </div>
  )
}


export default OptionsCard
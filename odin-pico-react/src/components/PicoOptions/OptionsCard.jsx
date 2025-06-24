import React from 'react';
import ChannelSetup from './Setup/ChannelSetup';
import GeneralSetup from './Setup/GeneralSetup';

import CaptureSettings from './Capture/CaptureSettings';
import GpibSettings from './GPIB/GpibSettings';

const OptionsCard = ({ pico_endpoint }) => {
  const [channelStates, setChannelStates] = React.useState([]);
  const anyChannelActive = channelStates.some(ch => ch.active);
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
            />
            <ChannelSetup
              channelStates={channelStates}
              setChannelStates={setChannelStates}
              anyActive={anyChannelActive}
              pico_endpoint={pico_endpoint}
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
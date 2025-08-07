import React from 'react';
import ChannelSetup from './Setup/ChannelSetup';
import GeneralSetup from './Setup/GeneralSetup';
import TriggerSetup from './Setup/TriggerSetup';
import PHASettings from './Setup/PHASettings';

import CaptureButtons from './Capture/CaptureButtons';
import CaptureSettings from './Capture/CaptureSettings';
import CaptureStatus from './Capture/CaptureStatus';

import GpibControl from './GPIB/GpibControl';
import GpibTecSet from './GPIB/GpibTecSet';
import GpibTecStatus from './GPIB/GpibTecStatus';
import GpibTempSweep from './GPIB/GpibTempSweep';

import { WithEndpoint } from 'odin-react';

const EndpointInput = WithEndpoint((props) => (
  <input {...props} className={`form small-text ${props.className || ''}`} />
));

const EndpointSelect = WithEndpoint((props) => (
  <select {...props} className={`form ${props.className || ''}`}>
    {props.children}
  </select>
));

const RadioGroup = ({ value, onChange, options = [], name, disabled, className = '', ...props }) => (
  <div className={`radio-group ${className}`} {...props}>
    {options.map(({ label, value: optionValue }) => (
      <label key={optionValue} style={{ marginRight: '1rem' }}>
        <input
          type="radio"
          name={name}
          value={optionValue}
          checked={String(value) === String(optionValue)}
          onChange={(e) => {
            const raw = e.target.value;
            let parsed;

            if (raw === 'true') {
              parsed = true;
            } else if (raw === 'false') {
              parsed = false;
            } else if (!isNaN(raw)) {
              parsed = Number(raw);
            } else {
              parsed = raw;
            }

            onChange({ target: { value: parsed } });
          }}
          disabled={disabled}
        />
        {' '}{label}
      </label>
    ))}
  </div>
);
const EndpointRadioGroup = WithEndpoint(RadioGroup);

const ToggleSwitch = ({ className = '', ...props }) => (
  <label className={`switch ${className}`}>
    <input type="checkbox" {...props} />
    <span className="slider round"></span>
  </label>
);
const EndpointToggleSwitch = WithEndpoint(ToggleSwitch);

const OptionsCard = ({ pico_endpoint }) => {

  const [gpibEnabled, setGpibEnabled] = React.useState(false);
  const channels = pico_endpoint?.data?.device?.settings?.channels;
  const captureRunning = pico_endpoint?.data?.device?.commands?.run_user_capture;
  const temperatureSweepActive = pico_endpoint?.data?.gpib?.temp_sweep?.active;

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
              EndpointRadioGroup={EndpointRadioGroup}
              captureRunning={captureRunning}
            />
            <ChannelSetup
              anyActive={anyChannelActive}
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              EndpointSelect={EndpointSelect}
              EndpointToggleSwitch={EndpointToggleSwitch}
              captureRunning={captureRunning}
            />
            <TriggerSetup
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              EndpointSelect={EndpointSelect}
              EndpointToggleSwitch={EndpointToggleSwitch}
              captureRunning={captureRunning}
            />
            <PHASettings
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              captureRunning={captureRunning}
            />
          </>
        )}
        {activeTab === 'capture' && (
          <>
            <CaptureButtons
              pico_endpoint={pico_endpoint}
              captureRunning={captureRunning}
            />
            <CaptureStatus
              pico_endpoint={pico_endpoint}
              captureRunning={captureRunning}
            />
            <CaptureSettings
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              EndpointRadioGroup={EndpointRadioGroup}
              captureRunning={captureRunning}
            />
          </>
        )}
        {activeTab === 'gpib' && gpibEnabled && (
          <>
            <GpibControl
              pico_endpoint={pico_endpoint}
              EndpointSelect={EndpointSelect}
              EndpointToggleSwitch={EndpointToggleSwitch}
              EndpointRadioGroup={EndpointRadioGroup}
              captureRunning={captureRunning}
            />
            {temperatureSweepActive ? (
              <GpibTempSweep
                pico_endpoint={pico_endpoint}
                EndpointInput={EndpointInput}
                captureRunning={captureRunning}
              />
            ) : (
              <GpibTecSet
                pico_endpoint={pico_endpoint}
                EndpointInput={EndpointInput}
                captureRunning={captureRunning}
              />
            )}
            <GpibTecStatus
              pico_endpoint={pico_endpoint}
            />
          </> 
          )}
      </div>
    </div>
  )
}


export default OptionsCard
import UICard from '../utils/UICard';

import InfoBar from './InfoBar';

import ChannelSetup from './Setup/ChannelSetup';
import GeneralSetup from './Setup/GeneralSetup';
import TriggerSetup from './Setup/TriggerSetup';
import PHASettings from './Setup/PHASettings';

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

const ToggleSwitch = ({ className = '', ...props }) => (
  <label className={`switch ${className}`}>
    <input type="checkbox" {...props} />
    <span className="slider round"></span>
  </label>
);
const EndpointToggleSwitch = WithEndpoint(ToggleSwitch);

const OptionsCard = ({ pico_endpoint, activeTab }) => {

  const channels = pico_endpoint?.data?.device?.settings?.channels;
  const captureRunning = pico_endpoint?.data?.device?.commands?.run_user_capture;
  const temperatureSweepActive = pico_endpoint?.data?.gpib?.temp_sweep?.active;

  let anyChannelActive;

  if (channels !== undefined) {
      anyChannelActive = Object.values(channels).some(channel => channel.active);
  } else {
      anyChannelActive = false;
  }

  return (
    <div className="fixed-width" id="left-panel">
      <div className="tab-content p-3">

        <UICard title="Status" noTopMargin>
          <div style={{ padding: '10px' }}>
            <InfoBar pico_endpoint={pico_endpoint} />
          </div>
        </UICard>

        {activeTab === 'setup' && (
          <>
            <GeneralSetup
              anyActive={anyChannelActive}
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
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
            <CaptureSettings
              pico_endpoint={pico_endpoint}
              EndpointInput={EndpointInput}
              captureRunning={captureRunning}
            />
            <CaptureStatus
              pico_endpoint={pico_endpoint}
              captureRunning={captureRunning}
            />
          </>
        )}
        {activeTab === 'gpib' && (
          <>
            <GpibControl
              pico_endpoint={pico_endpoint}
              EndpointSelect={EndpointSelect}
              EndpointToggleSwitch={EndpointToggleSwitch}
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
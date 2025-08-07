import UICard from '../../utils/UICard';
import { getChannelRowClass, toSiUnit } from '../../utils/utils';
import '../Options.css';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const GeneralSetup = ({ pico_endpoint, anyActive, EndpointInput, captureRunning }) => {
  const verificationPath = pico_endpoint?.data?.device?.status;
  const hasInvalid = verificationPath === undefined? false : verificationPath.pico_setup_verify === 0 ? true : false;

  const baseRowClass = getChannelRowClass(true, anyActive);
  const rowClass = !hasInvalid ? 'bg-red' : baseRowClass;

  const settingsPath = pico_endpoint?.data?.device?.settings?.mode?.samp_time;
  const settings = settingsPath === undefined ? 'Processing...' : toSiUnit(settingsPath);

  return (
    <UICard title="General Setup">
      <table className="table mb-0">
        <tbody>
          <tr className={rowClass} id="general-setup-row">
            <th>
              <label htmlFor="bit-mode-dropdown">Resolution</label>
              <ButtonGroup size="sm" className="mb-2">
                {[
                  { name: '8 Bit', value: 0 },
                  { name: '12 Bit', value: 1 }
                ].map((radio, idx) => (
                  <ToggleButton
                    key={idx}
                    type="radio"
                    variant="outline-primary"
                    name="bit-mode"
                    value={radio.value.toString()}
                    checked={pico_endpoint?.data?.device?.settings?.mode?.resolution === radio.value}
                    onClick={() => pico_endpoint.put(radio.value, 'device/settings/mode/resolution')}
                    disabled={captureRunning}
                  >
                    {radio.name}
                  </ToggleButton>
                ))}
              </ButtonGroup>
            </th>

            <th>
              <label htmlFor="time-base-input">Timebase</label>
              <EndpointInput
                id="time-base-input"
                endpoint={pico_endpoint}
                fullpath="device/settings/mode/timebase"
                type="number"
                disabled={captureRunning}
              />
              <div>
                <span>Sample Interval: </span>
                <span>{settings}</span>
                <span>s</span>
              </div>
            </th>

            <th>
              <label htmlFor="capture-pretrig-samples">Pre-Trigger Samples</label>
              <EndpointInput
                id="capture-pretrig-samples"
                endpoint={pico_endpoint}
                fullpath="device/settings/capture/pre_trig_samples"
                type="number"
                disabled={captureRunning}
              />
            </th>

            <th>
              <label htmlFor="capture-posttrig-samples">Post-Trigger Samples</label>
              <EndpointInput
                id="capture-posttrig-samples"
                endpoint={pico_endpoint}
                fullpath="device/settings/capture/post_trig_samples"
                type="number"
                disabled={captureRunning}
              />
            </th>
          </tr>
        </tbody>
      </table>
    </UICard>
  );
};

export default GeneralSetup;

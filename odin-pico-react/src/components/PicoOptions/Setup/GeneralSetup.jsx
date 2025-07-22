import UICard from '../../utils/UICard';
import { getChannelRowClass, toSiUnit } from '../../utils/utils';
import '../Options.css';

const GeneralSetup = ({ pico_endpoint, anyActive, EndpointInput, EndpointSelect, captureRunning }) => {
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
              <EndpointSelect
                id="bit-mode-dropdown"
                endpoint={pico_endpoint}
                fullpath="device/settings/mode/resolution"
                type="number"
                disabled={captureRunning}
              >
                <option value="0">8 Bit Mode</option>
                <option value="1">12 Bit Mode</option>
              </EndpointSelect>
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

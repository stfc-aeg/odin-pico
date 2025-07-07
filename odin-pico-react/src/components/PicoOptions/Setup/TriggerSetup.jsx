import UICard from '../../utils/UICard';

const sourceOptions = [
  { value: 0, label: 'Channel A' },
  { value: 1, label: 'Channel B' },
  { value: 2, label: 'Channel C' },
  { value: 3, label: 'Channel D' },
];

const directionOptions = [
  { value: 0, label: 'Above' },
  { value: 1, label: 'Below' },
  { value: 2, label: 'Rising Edge' },
  { value: 3, label: 'Falling Edge' },
  { value: 4, label: 'Rising or Falling Edge' },
];

const rangeCodeToMillivolts = {
  0: 10,
  1: 20,
  2: 50,
  3: 100,
  4: 200,
  5: 500,
  6: 1000,
  7: 2000,
  8: 5000,
  9: 10000,
  10: 20000,
};

const TriggerSetup = ({ pico_endpoint, EndpointInput, EndpointSelect }) => {

  const getTriggerClass = () => {
    const verificationPath = pico_endpoint?.data?.device?.status?.channel_trigger_verify;
    const isValid = verificationPath === undefined? false : verificationPath === 0 ? true : false;

    const currentChannelIndex = pico_endpoint?.data?.device?.settings?.trigger?.source;
    const channelLetter = ['a', 'b', 'c', 'd'][currentChannelIndex];

    const channelData = pico_endpoint?.data?.device?.settings?.channels?.[channelLetter];
    const triggerThreshold = pico_endpoint?.data?.device?.settings?.trigger?.threshold;

    if (!channelData?.active) return 'bg-red';

    const channelRangeCode = channelData?.range;
    const channelRange = rangeCodeToMillivolts[channelRangeCode];

    if (isValid && triggerThreshold <= channelRange) {
      return 'bg-green';
    }

    return 'bg-red';
  }

  return (
    <div className="col-sm-12" id="trigger-setup-div">
      <UICard title="Trigger Setup">
        <table className="table" style={{ marginBottom: 0 }}>
          <tbody>
            <tr className={getTriggerClass()}>
              <th>
                <label htmlFor="trigger-enable">Enable:</label>
                <EndpointSelect
                  id="trigger-enable"
                  endpoint={pico_endpoint}
                  fullpath="device/settings/trigger/active"
                  className="form"
                >
                  <option value={true}>True</option>
                  <option value={false}>False</option>
                </EndpointSelect>
              </th>

              <th>
                <label htmlFor="trigger-source">Source:</label>
                <EndpointSelect
                  id="trigger-source"
                  endpoint={pico_endpoint}
                  fullpath="device/settings/trigger/source"
                >
                  {sourceOptions.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </EndpointSelect>
              </th>

              <th>
                <label htmlFor="trigger-direction">Signal Direction:</label>
                <EndpointSelect
                  id="trigger-direction"
                  endpoint={pico_endpoint}
                  fullpath="device/settings/trigger/direction"
                >
                  {directionOptions.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </EndpointSelect>
              </th>
            </tr>

            <tr className={getTriggerClass()}>
              <th>
                <label htmlFor="trigger-threshold">Threshold (mV):</label>
                <EndpointInput
                  id="trigger-threshold"
                  endpoint={pico_endpoint}
                  fullpath="device/settings/trigger/threshold"
                  type="number"
                />
              </th>

              <th>
                <label htmlFor="trigger-delay">Delay (ms):</label>
                <EndpointInput
                  id="trigger-delay"
                  endpoint={pico_endpoint}
                  fullpath="device/settings/trigger/delay"
                  type="number"
                />
              </th>

              <th>
                <label htmlFor="trigger-auto">Trigger After (ms):</label>
                <EndpointInput
                  id="trigger-auto"
                  endpoint={pico_endpoint}
                  fullpath="device/settings/trigger/auto_trigger"
                  type="number"
                />
              </th>
            </tr>
          </tbody>
        </table>
      </UICard>
    </div>
  );
};

export default TriggerSetup;

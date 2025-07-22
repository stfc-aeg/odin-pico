import UICard from '../../utils/UICard';

const PHASettings = ({ pico_endpoint, EndpointInput, captureRunning }) => {
  
  const is_pha_verified = pico_endpoint?.data?.device?.status?.capture_settings_verify;

  return (
    <UICard title="PHA Settings">
      <table className="table" style={{ marginBottom: 0 }}>
        <tbody>
          <tr className={is_pha_verified === 0 ? 'bg-green' : 'bg-red'}>
            <th>
              <label htmlFor="num_bins">Number Bins:</label>
              <EndpointInput
                id="num_bins"
                endpoint={pico_endpoint}
                fullpath="device/settings/pha/num_bins"
                type="number"
                disabled={captureRunning}
              />
            </th>
            <th>
              <label htmlFor="lower_range">Lower range of ADC_Counts:</label>
              <EndpointInput
                id="lower_range"
                endpoint={pico_endpoint}
                fullpath="device/settings/pha/lower_range"
                type="number"
                disabled={captureRunning}
              />
            </th>
            <th>
              <label htmlFor="upper_range">Upper range of ADC_Counts:</label>
              <EndpointInput
                id="upper_range"
                endpoint={pico_endpoint}
                fullpath="device/settings/pha/upper_range"
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

export default PHASettings;

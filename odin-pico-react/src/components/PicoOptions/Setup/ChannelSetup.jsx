import React from 'react';
import UICard from '../../utils/UICard';
import { getChannelRowClass } from '../../utils/utils';

const couplingOptions = [
  { value: '1', label: 'DC' },
  { value: '0', label: 'AC' },
];

const rangeOptions = [
  { value: '0', label: '10 mV' },
  { value: '1', label: '20 mV' },
  { value: '2', label: '50 mV' },
  { value: '3', label: '100 mV' },
  { value: '4', label: '200 mV' },
  { value: '5', label: '500 mV' },
  { value: '6', label: '1 V' },
  { value: '7', label: '2 V' },
  { value: '8', label: '5 V' },
  { value: '9', label: '10 V' },
  { value: '10', label: '20 V' },
];

const ChannelSetup = ({ channelStates, setChannelStates, anyActive, pico_endpoint }) => {
  const [loading, setLoading] = React.useState(true);

  // Initial GET fetch
  React.useEffect(() => {
    pico_endpoint.get('device/settings/channels')
      .then((response) => {
        const channelObj = response.channels;
        const formatted = Object.entries(channelObj).map(([id, data]) => ({
          id,
          label: id.toUpperCase(),
          active: data.active,
          coupling: String(data.coupling),
          range: String(data.range),
          offset: String(data.offset),
        }));
        setChannelStates(formatted);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching channel data:', err);
        setLoading(false);
      });
  }, []);

  // Update helper
  const updateChannel = (id, key, value) => {
    pico_endpoint.put({ [key]: value }, `device/settings/channels/${id}/`)
      .catch((err) => console.error(`Failed to update ${id}:${key}`, err));
  };

  const handleCheckboxChange = (index) => (e) => {
    const newChannels = [...channelStates];
    newChannels[index].active = e.target.checked;
    setChannelStates(newChannels);
    updateChannel(newChannels[index].id, 'active', e.target.checked);
  };

  const handleSelectChange = (index, field) => (e) => {
    const newChannels = [...channelStates];
    newChannels[index][field] = e.target.value;
    setChannelStates(newChannels);
    updateChannel(newChannels[index].id, field, parseInt(e.target.value));
  };

  const handleInputChange = (index) => (e) => {
    const value = e.target.value;
    const newChannels = [...channelStates];
    newChannels[index].offset = value;
    setChannelStates(newChannels);
    const floatVal = parseFloat(value);
    if (!isNaN(floatVal)) updateChannel(newChannels[index].id, 'offset', floatVal);
  };

  if (loading) return <p>Loading channel setup...</p>;

  return (
    <div className="col-sm-12" id="chan-6-div">
      <UICard title="Channel Setup">
        <table className="table" style={{ marginBottom: '0px' }}>
          <thead>
            <tr className={getChannelRowClass(true, anyActive)} id="chan-row">
              <th>Channel:</th>
              <th>Channel Coupling</th>
              <th>Channel Range</th>
              <th>Offset (%)</th>
            </tr>
          </thead>
          <tbody>
            {channelStates.map(({ id, label, active, coupling, range, offset }, i) => (
              <tr
                key={id}
                className={getChannelRowClass(active, anyActive)}
                id={`channel-${id}-set`}
              >
                <th>
                  <div>
                    <label htmlFor={`channel-${id}-active`}>
                      {label}&nbsp;&nbsp;&nbsp;&nbsp;
                    </label>
                    <input
                      type="checkbox"
                      id={`channel-${id}-active`}
                      checked={active}
                      onChange={handleCheckboxChange(i)}
                    />
                  </div>
                </th>
                <th>
                  <select
                    id={`channel-${id}-coupl`}
                    value={coupling}
                    onChange={handleSelectChange(i, 'coupling')}
                  >
                    {couplingOptions.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </th>
                <th>
                  <select
                    id={`channel-${id}-range`}
                    value={range}
                    onChange={handleSelectChange(i, 'range')}
                  >
                    {rangeOptions.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </th>
                <th>
                  <input
                    id={`channel-${id}-offset`}
                    type="text"
                    value={offset}
                    onChange={handleInputChange(i)}
                  />
                </th>
              </tr>
            ))}
          </tbody>
        </table>
      </UICard>
    </div>
  );
};

export default ChannelSetup;
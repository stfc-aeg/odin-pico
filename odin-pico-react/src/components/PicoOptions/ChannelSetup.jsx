import React from 'react';
import UICard from '../utils/UICard';
import { getChannelRowClass } from '../utils/utils';

const defaultChannels = [
  { id: 'a', label: 'A', active: false, coupling: '1', range: '0', offset: '0' },
  { id: 'b', label: 'B', active: false, coupling: '1', range: '0', offset: '0' },
  { id: 'c', label: 'C', active: false, coupling: '1', range: '0', offset: '0', danger: true },
  { id: 'd', label: 'D', active: false, coupling: '1', range: '0', offset: '0', danger: true },
];

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

const ChannelSetup = () => {
  const [channelStates, setChannelStates] = React.useState(defaultChannels);

  const anyActive = channelStates.some(ch => ch.active);

  const handleCheckboxChange = (index) => (e) => {
    const newChannels = [...channelStates];
    newChannels[index].active = e.target.checked;
    setChannelStates(newChannels);
    // Call new commit_checked_adapter here
  };

  const handleSelectChange = (index, field) => (e) => {
    const newChannels = [...channelStates];
    newChannels[index][field] = e.target.value;
    setChannelStates(newChannels);
    // Call new commit_int_adapter here
  };

  const handleInputChange = (index) => (e) => {
    const newChannels = [...channelStates];
    newChannels[index].offset = e.target.value;
    setChannelStates(newChannels);
    // Call new commit_float_adapter here
  };

  return (
    <div className="col-sm-12" id="chan-6-div">
      <UICard title="Channel Setup">
        <table className="table" style={{ marginBottom: '0px'}}>
        <thead>
          <tr className={anyActive ? "table-success" : "table-danger"} id="chan-row">
            <th>Channel:</th>
            <th>Channel Coupling</th>
            <th>Channel Range</th>
            <th>Offset (%)</th>
          </tr>
        </thead>
          <tbody>
            {channelStates.map(({ id, label, active, coupling, range, offset, danger }, i) => (
              <tr
                key={id}
                className={getChannelRowClass(active, anyActive)}
                id={`channel-${id}-set`}
              >
                <th>
                  <div className={`custom-div-${id}`}>
                    <label htmlFor={`channel-${id}-active`} className="custom-label">
                      {label}&nbsp;&nbsp;&nbsp;&nbsp;
                    </label>
                    <input
                      type="checkbox"
                      id={`channel-${id}-active`}
                      checked={active}
                      onChange={handleCheckboxChange(i)}
                      className="custom-checkbox"
                      value={i}
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

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

const ChannelSetup = ({ anyActive, pico_endpoint, EndpointInput, EndpointSelect, EndpointCheckbox }) => {
  const channelObj = pico_endpoint?.data?.device?.settings?.channels ?? {};
  const channelStates = Object.entries(channelObj).map(([id, data]) => ({
    id,
    label: id.toUpperCase(),
    active: data.active,
    coupling: String(data.coupling),
    range: String(data.range),
    offset: String(data.offset),
  }));
  const activeChannels = channelStates.filter(ch => ch.active);
  const allOffsetsInvalid = activeChannels.length > 0 && activeChannels.every(
    ch => Number(ch.offset) > 100 || Number(ch.offset) < -100
  );

  return (
    <div className="col-sm-12" id="chan-6-div">
      <UICard title="Channel Setup">
        <table className="table" style={{ marginBottom: '0px' }}>
          <thead>
            <tr className={allOffsetsInvalid ? 'bg-red' : getChannelRowClass(true, anyActive, true)} id="chan-row">
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
                className={(Number(offset) > 100 || Number(offset) < -100) ? 'bg-red' : getChannelRowClass(active, anyActive, true)}
                id={`channel-${id}-set`}
              >
                <th>
                  <div>
                    <label htmlFor={`channel-${id}-active`}>
                      {label}&nbsp;&nbsp;&nbsp;&nbsp;
                    </label>
                    <EndpointCheckbox
                      id={`channel-${id}-active`}
                      endpoint={pico_endpoint}
                      fullpath={`device/settings/channels/${id}/active`}
                    />
                  </div>
                </th>
                <th>
                  <EndpointSelect
                    id={`channel-${id}-coupl`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/coupling`}
                  >
                    {couplingOptions.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </EndpointSelect>
                </th>
                <th>
                  <EndpointSelect
                    id={`channel-${id}-range`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/range`}
                  >
                    {rangeOptions.map(({ value, label }) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </EndpointSelect>
                </th>
                <th>
                  <EndpointInput
                    id={`channel-${id}-offset`}
                    endpoint={pico_endpoint}
                    fullpath={`device/settings/channels/${id}/offset`}
                    type="number"
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
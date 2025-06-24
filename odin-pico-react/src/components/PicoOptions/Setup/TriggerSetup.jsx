import React from 'react';
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

const TriggerSetup = ({ pico_endpoint, activeChannels }) => {
  const [trigger, setTrigger] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    pico_endpoint.get('device/settings/trigger')
      .then(data => {
        setTrigger({ ...data.trigger });
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load trigger config', err);
        setLoading(false);
      });
  }, []);

  const handleUpdate = (key, value) => {
    const parsed = key === 'active' ? value === 'true' : parseInt(value, 10);
    setTrigger(prev => ({ ...prev, [key]: parsed }));

    pico_endpoint.put({ [key]: parsed }, 'device/settings/trigger')
      .catch(err => console.error(`Failed to update ${key}:`, err));
  };

  const getTriggerClass = () => {
    if (activeChannels.includes(trigger.source)) {
      return 'bg-green';
    }
    return 'bg-red';
  };

  if (loading || !trigger) return <p>Loading trigger setup...</p>;

  return (
    <div className="col-sm-12" id="trigger-setup-div">
      <UICard title="Trigger Setup">
        <table className="table" style={{ marginBottom: 0 }}>
          <tbody>
            <tr className={getTriggerClass()}>
              <th>
                <label htmlFor="trigger-enable">Enable:</label>
                <select
                  id="trigger-enable"
                  className="form"
                  value={String(trigger.active)}
                  onChange={(e) => handleUpdate('active', e.target.value)}
                >
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              </th>

              <th>
                <label htmlFor="trigger-source">Source:</label>
                <select
                  id="trigger-source"
                  className="form"
                  value={trigger.source}
                  onChange={(e) => handleUpdate('source', e.target.value)}
                >
                  {sourceOptions.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </th>

              <th>
                <label htmlFor="trigger-direction">Signal Direction:</label>
                <select
                  id="trigger-direction"
                  className="form"
                  value={trigger.direction}
                  onChange={(e) => handleUpdate('direction', e.target.value)}
                >
                  {directionOptions.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </th>
            </tr>

            <tr className={getTriggerClass()}>
              <th>
                <label htmlFor="trigger-threshold">Threshold (mV):</label>
                <input
                  id="trigger-threshold"
                  type="number"
                  className="form"
                  value={trigger.threshold}
                  onChange={(e) => handleUpdate('threshold', e.target.value)}
                />
              </th>

              <th>
                <label htmlFor="trigger-delay">Delay (ms):</label>
                <input
                  id="trigger-delay"
                  type="number"
                  min="0"
                  className="form"
                  value={trigger.delay}
                  onChange={(e) => handleUpdate('delay', e.target.value)}
                />
              </th>

              <th>
                <label htmlFor="trigger-auto">Trigger After (ms):</label>
                <input
                  id="trigger-auto"
                  type="number"
                  min="0"
                  className="form"
                  value={trigger.auto_trigger}
                  onChange={(e) => handleUpdate('auto_trigger', e.target.value)}
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

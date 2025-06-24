import React from 'react';
import UICard from '../../utils/UICard';
import { Form } from 'react-bootstrap';
import { getChannelRowClass, toSiUnit } from '../../utils/utils';
import '../Options.css'

const GeneralSetup = ({ pico_endpoint, anyActive }) => {
  const [settings, setSettings] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [invalidInputs, setInvalidInputs] = React.useState({});


  // Initial GET fetch
  React.useEffect(() => {
    pico_endpoint.get('device/settings')
      .then((response) => {
        setSettings(response.settings);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching device settings:', err);
        setLoading(false);
      });
  }, [pico_endpoint]);

  const commitIntAdapter = (id, path, key) => {
    const inputElem = document.getElementById(id);
    const value = parseInt(inputElem.value);

    if (isNaN(value) || value < 0) {
      setInvalidInputs(prev => ({ ...prev, [id]: true }));
      console.warn(`Invalid input for ${key}`);
      return;
    } else {
      setInvalidInputs(prev => ({ ...prev, [id]: false }));
    }

    const data = {};
    data[key] = value;

    pico_endpoint.put(data, `device/settings/${path}`).catch(err => {
      console.error(`PUT failed for ${key}`, err);
    });
  };

  if (loading || !settings) return null;

  const baseRowClass = getChannelRowClass(true, anyActive);
  const hasInvalid = Object.values(invalidInputs).some(v => v);
  const rowClass = hasInvalid ? 'bg-red' : baseRowClass;

  return (
    <UICard title="General Setup">
      <table className="table mb-0">
        <tbody>
          <tr className={rowClass} id="general-setup-row">
          <th>
              <Form.Group controlId="bit-mode-dropdown">
                <Form.Label>Resolution</Form.Label>
                <Form.Control
                  as="select"
                  onChange={() => commitIntAdapter('bit-mode-dropdown', 'mode/', 'resolution')}
                  defaultValue={settings.mode.resolution}
                >
                  <option value="0">8 Bit Mode</option>
                  <option value="1">12 Bit Mode</option>
                </Form.Control>
              </Form.Group>
            </th>
            <th>
              <Form.Group controlId="time-base-input">
                <Form.Label>Timebase</Form.Label>
                <Form.Control
                  type="text"
                  className={`small-text`}
                  defaultValue={settings.mode.timebase}
                  onChange={() => commitIntAdapter('time-base-input', 'mode/', 'timebase')}
                />
                <div>
                  <span>Sample Interval: </span>
                  <span>{toSiUnit(settings.mode.samp_time)}</span>
                  <span>s</span>
                </div>
              </Form.Group>
            </th>
            <th>
              <Form.Group controlId="capture-pretrig-samples">
                <Form.Label>Pre-Trigger Samples</Form.Label>
                <Form.Control
                  type="text"
                  className={`small-text`}
                  defaultValue={settings.capture.pre_trig_samples}
                  onChange={() => commitIntAdapter('capture-pretrig-samples', 'capture/', 'pre_trig_samples')}
                />
              </Form.Group>
            </th>
            <th>
              <Form.Group controlId="capture-posttrig-samples">
                <Form.Label>Post-Trigger Samples</Form.Label>
                <Form.Control
                  type="text"
                  className={`small-text`}
                  defaultValue={settings.capture.post_trig_samples}
                  onChange={() => commitIntAdapter('capture-posttrig-samples', 'capture/', 'post_trig_samples')}
                />
              </Form.Group>
            </th>
          </tr>
        </tbody>
      </table>
    </UICard>
  );
};

export default GeneralSetup;

import UICard from '../../utils/UICard';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

import { WithEndpoint } from 'odin-react';
import Form from 'react-bootstrap/Form';

const EndpointSwitch = WithEndpoint(({ ...props }) => (
    <Form.Check
        type="switch"
        {...props}
    />
));

const CaptureSettings = ({ pico_endpoint, EndpointInput }) => {
    const rowClass = 'bg-empty';

    const capturePath = pico_endpoint?.data?.device?.settings?.capture ?? {};
    const captureMode = capturePath?.capture_mode;
    const acquisitionEnabled = capturePath?.capture_repeat;

    const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};
    const filename = fileSettingsPath?.file_path + fileSettingsPath?.folder_name + fileSettingsPath?.file_name;

    const settingsTitle = captureMode ? "Capture Time (Seconds):" : "Number of Captures:";
    const settingsPath = captureMode ? "capture_time" : "n_captures";
    const recMax = captureMode ? "max_time" : "max_captures";

    const settingsValue = captureMode ? "Capture Time" : "Number of Captures";
    const acquisitionNumber = acquisitionEnabled ? "Repeated Acquisition" : "Single Acquisition";

    const captureModeSettingsRadios = [
        { name: 'Number of Captures', value: 'Number of Captures' },
        { name: 'Capture Time', value: 'Capture Time' }
    ];
    const acquisitionNumberRadios = [
        { name: 'Single Acquisition', value: 'Single Acquisition' },
        { name: 'Repeated Acquisition', value: 'Repeated Acquisition' }
    ]
    const handleRadioValueChange = (newValue, comp, path) => {
        let capMode = newValue === comp;
        pico_endpoint.put(!capMode, path);
    }

    return (
        <>
            <UICard title="Capture Settings">
                <table className="table mb-0">
                    <tbody>
                        <tr className={rowClass}>
                            <th className="align-middle">
                                <ButtonGroup size="sm" className="mb-2">
                                    {captureModeSettingsRadios.map((radio, idx) => (
                                        <ToggleButton
                                        key={idx}
                                        type="radio"
                                        variant="outline-primary"
                                        name="captureModeSettingsRadio"
                                        value={radio.value}
                                        checked={settingsValue === radio.value}
                                        onClick={() => handleRadioValueChange(radio.value, 'Number of Captures', 'device/settings/capture/capture_mode')}>
                                            {radio.name}
                                        </ToggleButton>
                                    ))}
                                </ButtonGroup>
                            </th>
                            <th colspan="2" className="align-middle">
                                <label>{settingsTitle}</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath={`device/settings/capture/${settingsPath}`}
                                    type="number"
                                />
                                <div>
                                    <span>Recommended Max : </span>
                                    <span>{capturePath?.[recMax]}</span>
                                </div>
                            </th>
                        </tr>
                        <tr className={rowClass}>
                            <th className="align-middle">
                                <ButtonGroup size="sm" className="mb-2">
                                    {acquisitionNumberRadios.map((radio, idx) => (
                                        <ToggleButton
                                        key={idx}
                                        type="radio"
                                        variant="outline-primary"
                                        name="acquisitionNumberRadio"
                                        value={radio.value}
                                        checked={acquisitionNumber === radio.value}
                                        onClick={() => handleRadioValueChange(radio.value, 'Single Acquisition', 'device/settings/capture/capture_repeat')}>
                                            {radio.name}
                                        </ToggleButton>
                                    ))}
                                </ButtonGroup>
                                {/* <label>Enable Repeat Acquisition</label>
                                <div style={{ transform: 'scale(1.5)', transformOrigin: 'left center', maxWidth: '70px' }}>
                                    <EndpointSwitch
                                        endpoint={pico_endpoint}
                                        fullpath='device/settings/capture/capture_repeat'
                                        id="capture_repeat_switch"
                                    />
                                </div> */}
                            </th>
                            <th className="align-middle">
                                <label>Number of Acquisitions:</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/capture/repeat_amount'
                                    type="number"
                                    disabled={!acquisitionEnabled}
                                />
                            </th>
                            <th className="align-middle">
                                <label>Delay Time (Seconds):</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/capture/capture_delay'
                                    type="number"
                                    disabled={!acquisitionEnabled}
                                />
                            </th>
                        </tr>
                        <tr className={rowClass}>
                            <th className="align-middle">
                                <label>Folder Name:</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/file/folder_name'
                                />
                            </th>
                            <th className="align-middle">
                                <label>File Name:</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/file/file_name'
                                />
                            </th>
                            <th className="align-middle" style={{ fontSize: '12px' }}>
                                Filename Preview:<br/>
                                {filename}
                            </th>
                        </tr>
                    </tbody>
                </table>
            </UICard>
        </>
    )
}

export default CaptureSettings

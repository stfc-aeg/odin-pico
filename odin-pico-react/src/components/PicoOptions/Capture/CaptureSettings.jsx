import UICard from '../../utils/UICard';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const CaptureSettings = ({ pico_endpoint, EndpointInput, captureRunning }) => {
    const fileClass = pico_endpoint?.data?.device?.status?.file_name_verify ? 'bg-green' : 'bg-red';

    const capturePath = pico_endpoint?.data?.device?.settings?.capture ?? {};
    const captureMode = capturePath?.capture_mode;
    const acquisitionEnabled = capturePath?.capture_repeat;

    const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};
    const filename = fileSettingsPath?.file_path + fileSettingsPath?.folder_name + fileSettingsPath?.file_name;

    const settingsTitle = captureMode ? "Capture Time (Seconds)" : "Number of Captures";
    const settingsPath = captureMode ? "capture_time" : "n_captures";
    const recMax = captureMode ? "max_time" : "max_captures";

    return (
        <>
            <UICard title="Capture Settings">
                <table className="table mb-0">
                    <tbody>
                        <tr>
                            <th className="align-middle">
                                Capture mode: &nbsp;
                                <ButtonGroup size="sm" className="mb-2">
                                    {[
                                        { name: 'Number', value: false },
                                        { name: 'Time', value: true }
                                    ].map((radio, idx) => (
                                        <ToggleButton
                                            key={idx}
                                            type="radio"
                                            variant="outline-primary"
                                            name="captureModeSettingsRadio"
                                            value={radio.value.toString()}
                                            checked={pico_endpoint?.data?.device?.settings?.capture?.capture_mode === radio.value}
                                            onClick={() => pico_endpoint.put(radio.value, 'device/settings/capture/capture_mode')}
                                            disabled={captureRunning}
                                            className={pico_endpoint?.data?.device?.settings?.capture?.capture_mode !== radio.value ? 'bg-white' : ''}
                                        >
                                            {radio.name}
                                        </ToggleButton>
                                    ))}
                                </ButtonGroup>
                            </th>
                            <th colSpan="2" className="align-middle">
                                <label>{settingsTitle}</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath={`device/settings/capture/${settingsPath}`}
                                    type="number"
                                    disabled={captureRunning}
                                />
                                <div style={{ fontWeight: 'normal' }}>
                                    <span>Recommended Max : </span>
                                    <span>{capturePath?.[recMax]}</span>
                                </div>
                            </th>
                        </tr>
                        <tr>
                            <th className="align-middle">
                                Acquisition: &nbsp;&nbsp;
                                <ButtonGroup size="sm" className="mb-2">
                                    {[
                                        { name: 'Single', value: false },
                                        { name: 'Repeated', value: true }
                                    ].map((radio, idx) => (
                                        <ToggleButton
                                            key={idx}
                                            type="radio"
                                            variant="outline-primary"
                                            name="acquisitionNumberRadio"
                                            value={radio.value.toString()}
                                            checked={pico_endpoint?.data?.device?.settings?.capture?.capture_repeat === radio.value}
                                            onClick={() => pico_endpoint.put(radio.value, 'device/settings/capture/capture_repeat')}
                                            disabled={captureRunning}
                                            className={pico_endpoint?.data?.device?.settings?.capture?.capture_repeat !== radio.value ? 'bg-white' : ''}
                                        >
                                            {radio.name}
                                        </ToggleButton>
                                    ))}
                                </ButtonGroup>
                            </th>
                            <th className="align-middle">
                                <label>Number of Acquisitions</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/capture/repeat_amount'
                                    type="number"
                                    disabled={!acquisitionEnabled || captureRunning}
                                />
                            </th>
                            <th className="align-middle">
                                <label>Delay Time (Seconds)</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/capture/capture_delay'
                                    type="number"
                                    disabled={!acquisitionEnabled || captureRunning}
                                />
                            </th>
                        </tr>
                        <tr className={fileClass}>
                            <th className="align-middle">
                                <label>Folder Name</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/file/folder_name'
                                    disabled={captureRunning}
                                />
                            </th>
                            <th className="align-middle">
                                <label>File Name</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/file/file_name'
                                    disabled={captureRunning}
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

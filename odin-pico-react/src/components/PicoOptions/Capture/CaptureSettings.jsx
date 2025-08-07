import UICard from '../../utils/UICard';

const CaptureSettings = ({ pico_endpoint, EndpointInput, EndpointRadioGroup, captureRunning }) => {
    const fileClass = pico_endpoint?.data?.device?.status?.file_name_verify ? 'bg-green' : 'bg-red';

    const capturePath = pico_endpoint?.data?.device?.settings?.capture ?? {};
    const captureMode = capturePath?.capture_mode;
    const acquisitionEnabled = capturePath?.capture_repeat;

    const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};
    const filename = fileSettingsPath?.file_path + fileSettingsPath?.folder_name + fileSettingsPath?.file_name;

    const settingsTitle = captureMode ? "Capture Time (Seconds):" : "Number of Captures:";
    const settingsPath = captureMode ? "capture_time" : "n_captures";
    const recMax = captureMode ? "max_time" : "max_captures";

    return (
        <>
            <UICard title="Capture Settings">
                <table className="table mb-0">
                    <tbody>
                        <tr>
                            <th className="align-middle">
                                <EndpointRadioGroup
                                    endpoint={pico_endpoint}
                                    fullpath="device/settings/capture/capture_mode"
                                    name="captureModeSettingsRadio"
                                    options={[
                                        { label: 'Number of Captures', value: false },
                                        { label: 'Capture Time', value: true },
                                    ]}
                                    disabled={captureRunning}
                                />
                            </th>
                            <th colSpan="2" className="align-middle">
                                <label>{settingsTitle}</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath={`device/settings/capture/${settingsPath}`}
                                    type="number"
                                    disabled={captureRunning}
                                />
                                <div>
                                    <span>Recommended Max : </span>
                                    <span>{capturePath?.[recMax]}</span>
                                </div>
                            </th>
                        </tr>
                        <tr>
                            <th className="align-middle">
                                <EndpointRadioGroup
                                    endpoint={pico_endpoint}
                                    fullpath="device/settings/capture/capture_repeat"
                                    name="acquisitionNumberRadio"
                                    options={[
                                        { label: 'Single Acquisition', value: false },
                                        { label: 'Repeated Acquisition', value: true },
                                    ]}
                                    disabled={captureRunning}
                                />
                            </th>
                            <th className="align-middle">
                                {acquisitionEnabled ? (
                                    <>
                                        <label>Number of Acquisitions:</label>
                                        <EndpointInput
                                            endpoint={pico_endpoint}
                                            fullpath='device/settings/capture/repeat_amount'
                                            type="number"
                                            disabled={!acquisitionEnabled || captureRunning}
                                        />
                                    </>
                                ) : null}
                            </th>
                            <th className="align-middle">
                                {acquisitionEnabled ? (
                                    <>
                                        <label>Delay Time (Seconds):</label>
                                        <EndpointInput
                                            endpoint={pico_endpoint}
                                            fullpath='device/settings/capture/capture_delay'
                                            type="number"
                                            disabled={!acquisitionEnabled || captureRunning}
                                        />
                                    </>
                                ) : null}
                            </th>
                        </tr>
                        <tr className={fileClass}>
                            <th className="align-middle">
                                <label>Folder Name:</label>
                                <EndpointInput
                                    endpoint={pico_endpoint}
                                    fullpath='device/settings/file/folder_name'
                                    disabled={captureRunning}
                                />
                            </th>
                            <th className="align-middle">
                                <label>File Name:</label>
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

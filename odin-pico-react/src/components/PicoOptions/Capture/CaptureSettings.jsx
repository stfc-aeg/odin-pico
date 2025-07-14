import UICard from '../../utils/UICard';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const CaptureSettings = ({ pico_endpoint, EndpointInput }) => {
    const rowClass = 'bg-green';

    const capturePath = pico_endpoint?.data?.device?.settings?.capture ?? {};
    const captureMode = capturePath?.capture_mode;

    const settingsTitle = captureMode ? "Capture Time (Seconds):" : "Number of Captures:";
    const settingsPath = captureMode ? "capture_time" : "n_captures";
    const recMax = captureMode ? "max_time" : "max_captures";

    const settingsValue = captureMode ? "Capture Time" : "Number of Captures"

    const captureModeSettingsRadios = [
        { name: 'Number of Captures', value: 'Number of Captures' },
        { name: 'Capture Time', value: 'Capture Time' }
    ];
    const handleRadioValueChange = (newValue) => {
        let capMode = newValue === 'Number of Captures';
        pico_endpoint.put(!capMode, 'device/settings/capture/capture_mode');
    }

    return (
        <>
            <UICard title="Capture Mode Settings">
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
                                        onClick={() => handleRadioValueChange(radio.value)}>
                                            {radio.name}
                                        </ToggleButton>
                                    ))}
                                </ButtonGroup>
                            </th>
                            <th className="align-middle">
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
                    </tbody>
                </table>
            </UICard>
        </>
    )
}

export default CaptureSettings

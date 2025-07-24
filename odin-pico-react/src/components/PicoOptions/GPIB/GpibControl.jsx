import UICard from '../../utils/UICard';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const GpibControl = ({ pico_endpoint, EndpointSelect, captureRunning }) => {
    const availableTecs = pico_endpoint?.data?.gpib?.available_tecs;

    const gpibEndabled = pico_endpoint?.data?.gpib?.gpib_control;
    const gpibValue = gpibEndabled ? "GPIB enabled" : "GPIB disabled";
    const gpibEnabledRadios = [
        { name: 'GPIB disabled', value: 'GPIB disabled' },
        { name: 'GPIB enabled', value: 'GPIB enabled' }
    ];

    const outputControl = pico_endpoint?.data?.gpib?.output_state;
    const outputValue = outputControl ? "on" : "off";
    const outputStateRadios = [
        { name: 'Output Off', value: 'off' },
        { name: 'Output On', value: 'on' }
    ];

    const tempActive = pico_endpoint?.data?.gpib?.temp_sweep?.active;
    const cardActive = tempActive ? "Temperature Sweep" : "Single Shot";
    const cardToggleRadios = [
        { name: 'Single Shot', value: 'Single Shot' },
        { name: 'Temperature Sweep', value: 'Temperature Sweep' }
    ];

    
    const handleRadioValueChange = (newValue, comp, path) => {
        let capMode = newValue === comp;
        pico_endpoint.put(!capMode, path);
    }

    return (
        <UICard title="Control">
            <table className="table mb-0">
                <tbody>
                    <tr>
                        <th>
                            <ButtonGroup size="sm" className="mb-2">
                                {gpibEnabledRadios.map((radio, idx) => (
                                    <ToggleButton
                                    key={idx}
                                    type="radio"
                                    variant="outline-primary"
                                    name="gpibEnabledRadio"
                                    value={radio.value}
                                    checked={gpibValue === radio.value}
                                    onClick={() => handleRadioValueChange(radio.value, 'GPIB disabled', 'gpib/gpib_control')}
                                    disabled={captureRunning}>
                                        {radio.name}
                                    </ToggleButton>
                                ))}
                            </ButtonGroup>
                        </th>

                        <th>
                            
                            <ButtonGroup size="sm" className="mb-2">
                                {outputStateRadios.map((radio, idx) => (
                                    <ToggleButton
                                    key={idx}
                                    type="radio"
                                    variant="outline-primary"
                                    name="outputStateRadio"
                                    value={radio.value}
                                    checked={outputValue === radio.value}
                                    onClick={() => handleRadioValueChange(radio.value, 'off', 'gpib/output_state')}
                                    disabled={captureRunning}>
                                        {radio.name}
                                    </ToggleButton>
                                ))}
                            </ButtonGroup>
                        </th>

                        <th>
                            <ButtonGroup size="sm" className="mb-2">
                                {cardToggleRadios.map((radio, idx) => (
                                    <ToggleButton
                                    key={idx}
                                    type="radio"
                                    variant="outline-primary"
                                    name="cardToggleRadio"
                                    value={radio.value}
                                    checked={cardActive === radio.value}
                                    onClick={() => handleRadioValueChange(radio.value, 'Single Shot', 'gpib/temp_sweep/active')}
                                    disabled={captureRunning}>
                                        {radio.name}
                                    </ToggleButton>
                                ))}
                            </ButtonGroup>
                        </th>

                        <th>
                            Device:
                            <EndpointSelect
                                id="bit-mode-dropdown"
                                endpoint={pico_endpoint}
                                fullpath="gpib/selected_tec"
                                type="number"
                                disabled={captureRunning}
                            >
                                {availableTecs.map((tec, idx) => (
                                    <option key={idx} value={tec}>
                                        {tec}
                                    </option>
                                ))}
                            </EndpointSelect>
                        </th>
                    </tr>
                </tbody>
            </table>
        </UICard>
    )
}

export default GpibControl
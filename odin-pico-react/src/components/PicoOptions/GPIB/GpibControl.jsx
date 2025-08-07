import UICard from '../../utils/UICard';

const GpibControl = ({ pico_endpoint, EndpointSelect, EndpointToggleSwitch, EndpointRadioGroup, captureRunning }) => {
    const availableTecs = pico_endpoint?.data?.gpib?.available_tecs;

    return (
        <UICard title="Control">
            <table className="table mb-0">
                <tbody>
                    <tr>
                        <th className="align-middle">
                            <div>Enable: </div>
                            <EndpointToggleSwitch
                                endpoint={pico_endpoint}
                                fullpath="gpib/gpib_control"
                                disabled={captureRunning}
                            />
                        </th>

                        <th className="align-middle">
                            <div>Output: </div>
                            <EndpointToggleSwitch
                                endpoint={pico_endpoint}
                                fullpath="gpib/output_state"
                                disabled={captureRunning}
                            />
                        </th>

                        <th>
                            <EndpointRadioGroup
                                endpoint={pico_endpoint}
                                fullpath="gpib/temp_sweep/active"
                                name="cardToggleRadio"
                                options={[
                                    { label: 'Single Shot', value: false },
                                    { label: 'Temperature Sweep', value: true },
                                ]}
                                disabled={captureRunning}
                            />
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
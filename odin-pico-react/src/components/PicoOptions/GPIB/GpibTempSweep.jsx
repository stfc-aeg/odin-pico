import UICard from '../../utils/UICard';

const GpibTempSweep = ({ pico_endpoint, EndpointInput, captureRunning }) => {
    return (
        <UICard title="Temperature Sweep">
            <table className="table mb-0">
                <tbody>
                    <tr>
                        <th>
                            Start °C
                            <EndpointInput
                                endpoint={pico_endpoint}
                                fullpath="gpib/temp_sweep/t_start"
                                type="number"
                                disabled={captureRunning}
                            />
                        </th>

                        <th>
                            End °C
                            <EndpointInput
                                endpoint={pico_endpoint}
                                fullpath="gpib/temp_sweep/t_end"
                                type="number"
                                disabled={captureRunning}
                            />
                        </th>
                    </tr>
                    <tr>
                        <th>
                            Step °C
                            <EndpointInput
                                endpoint={pico_endpoint}
                                fullpath="gpib/temp_sweep/t_step"
                                type="number"
                                disabled={captureRunning}
                            />
                        </th>

                        <th>
                            Tolerance °C
                            <EndpointInput
                                endpoint={pico_endpoint}
                                fullpath="gpib/temp_sweep/tol"
                                type="number"
                                disabled={captureRunning}
                            />
                        </th>
                    </tr>
                </tbody>
            </table>
        </UICard>
    )
}

export default GpibTempSweep
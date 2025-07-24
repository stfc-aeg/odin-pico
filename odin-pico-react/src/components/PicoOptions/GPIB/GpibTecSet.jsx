import UICard from '../../utils/UICard';

const GpibTecSet = ({ pico_endpoint, EndpointInput, captureRunning }) => {
    const handleButtonClick = (path) => {
        pico_endpoint.put(true, path);
    };

    return (
        <UICard title="Single-Shot TEC Set">
            <table className="table mb-0">
                <tbody>
                    <tr>
                        <th>
                            Target °C:
                            <EndpointInput
                                endpoint={pico_endpoint}
                                fullpath="gpib/set/temp_target"
                                type="number"
                                disabled={captureRunning}
                            />
                        </th>

                        <th>
                            <button
                                className="btn btn-success"
                                onClick={() => handleButtonClick("gpib/set/set_temp")}
                                disabled={captureRunning}
                            >
                                Set
                            </button>
                        </th>
                    </tr>
                </tbody>
            </table>
        </UICard>
    )
}

export default GpibTecSet
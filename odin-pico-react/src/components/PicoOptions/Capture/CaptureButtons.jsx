import UICard from '../../utils/UICard';

const CaptureButtons = ({ pico_endpoint, captureRunning }) => {
    const handleButtonClick = (path) => {
        pico_endpoint.put(true, path);
    };

    return (
        <>
            <UICard title="Capture Buttons">
                <table className="table mb-0" style={{ fontSize: '14px' }}>
                    <tbody>
                        <tr>
                            <th className="align-middle">
                                <div>Record PicoScope Traces and PHA to File:</div>
                                <button
                                    className="btn btn-success"
                                    onClick={() => handleButtonClick("device/commands/run_user_capture")}
                                    disabled={captureRunning}
                                >
                                    Capture
                                </button>
                            </th>
                            <th className="align-middle">
                                <div>Abort Current Capture:</div>
                                <button
                                    className="btn btn-danger"
                                    onClick={() => handleButtonClick("device/flags/abort_cap")}
                                >
                                    Abort
                                </button>
                            </th>
                        </tr>
                    </tbody>
                </table>
            </UICard>
        </>
    )
}

export default CaptureButtons

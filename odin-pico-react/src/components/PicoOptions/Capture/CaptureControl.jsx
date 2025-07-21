import UICard from '../../utils/UICard';
import ProgressBar from './ProgressBar';

const CaptureControl = ({ pico_endpoint, EndpointInput }) => {
    const rowClass = 'bg-empty';
    const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};

    const file = fileSettingsPath?.curr_file_name;
    const recorded = fileSettingsPath?.last_write_success ? "True" : "False";

    const handleButtonClick = (path) => {
        pico_endpoint.put(true, path);
    };

    return (
        <>
            <UICard title="Capture Control">
                <table className="table mb-0" style={{ fontSize: '14px' }}>
                    <tbody>
                        <tr className={rowClass}>
                            <th className="align-middle">
                                <div>Record PicoScope Traces and PHA to File:</div>
                                <button
                                    className="btn btn-success"
                                    onClick={() => handleButtonClick("device/commands/run_user_capture")}
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
                        <tr className={rowClass}>
                            <th className="align-middle">
                                File:<br/>
                                {file}
                            </th>
                            <th className="align-middle">
                                Recorded:<br/>
                                {recorded}
                            </th>
                        </tr>
                        <tr className={rowClass}>
                            <th colspan="2" className="align-middle">
                                <ProgressBar
                                    response={pico_endpoint?.data}
                                />
                            </th>
                        </tr>
                    </tbody>
                </table>
            </UICard>
        </>
    )
}

export default CaptureControl

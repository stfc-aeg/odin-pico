import UICard from '../../utils/UICard';
import ProgressBar from './ProgressBar';

const CaptureStatus = ({ pico_endpoint, captureRunning }) => {
    const progressClass = captureRunning ? 'bg-green' : '';
    const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};

    const file = fileSettingsPath?.curr_file_name;
    const recorded = fileSettingsPath?.last_write_success ? "True" : "False";
    const systemState = pico_endpoint?.data?.device?.flags?.system_state;

    return (
        <>
            <UICard title="Capture Status">
                <table className="table mb-0" style={{ fontSize: '14px' }}>
                    <tbody>
                        <tr>
                            <th className="align-middle">
                                File:<br/>
                                {file}
                            </th>
                            <th className="align-middle">
                                Recorded:<br/>
                                {recorded}
                            </th>
                        </tr>
                        <tr>
                            <label>
                                System State:<br/>
                                {systemState}
                            </label>
                        </tr>
                        <tr className={progressClass}>
                            <th colSpan="2" className="align-middle">
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

export default CaptureStatus

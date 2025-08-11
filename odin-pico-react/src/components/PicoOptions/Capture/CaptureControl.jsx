import UICard from '../../utils/UICard';
import CaptureButton from './CaptureButton';

const CaptureControl = ({ pico_endpoint, captureRunning }) => {
    return (
        <>
            <UICard title="Capture Commands">
                <CaptureButton pico_endpoint={pico_endpoint} captureRunning={captureRunning} />
            </UICard>
        </>
    )
}

export default CaptureControl

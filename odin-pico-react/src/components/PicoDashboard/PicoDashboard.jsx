import OptionsCard from '../PicoOptions/OptionsCard';
import GraphCard from '../PicoGraph/GraphCard';

const PicoDashboard = ({ pico_endpoint, activeTab }) => {
    return (
        <>
            <div className="d-flex flex-wrap border rounded-1 pt-2 mt-2 ms-3 me-4">
                <div className="pe-3 ps-4" style={{ flexGrow: 1, width: '45%', minWidth: '620px' }}>
                    <OptionsCard pico_endpoint={pico_endpoint} activeTab={activeTab} />
                </div>
                <div className="ps-4 pe-3" style={{ flexGrow: 1, width: '55%', minWidth: '600px' }}>
                    <GraphCard pico_endpoint={pico_endpoint} />
                </div>
            </div>
        </>

    )
}

export default PicoDashboard
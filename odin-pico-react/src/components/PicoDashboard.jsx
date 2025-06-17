import OptionsCard from './OptionsCard';
import GraphCard from './GraphCard';

const PicoDashboard = () => {
    return (
        <>
            <div className="d-flex flex-wrap border rounded-1 pt-2 mt-2 ms-3 me-4">
                <div className="pe-3 ps-4" style={{ width: '45%', minWidth: '400px' }}>
                    <OptionsCard />
                </div>
                <div className="ps-4 pe-3" style={{ width: '55%' }}>
                    <GraphCard />
                </div>
            </div>
        </>

    )
}

// needs to be a flax box thing like the other code I made (wraps underneath)
// needs a line box thing around it

export default PicoDashboard
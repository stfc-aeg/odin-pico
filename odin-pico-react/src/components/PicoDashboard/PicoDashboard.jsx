import OptionsCard from '../PicoOptions/OptionsCard';
import GraphCard from '../PicoGraph/GraphCard';

const PicoDashboard = () => {
    return (
        <>
            <div className="d-flex flex-wrap border rounded-1 pt-2 mt-2 ms-3 me-4">
                <div className="pe-3 ps-4" style={{ flexGrow: 1, width: '40%', minWidth: '480px' }}>
                    <OptionsCard />
                </div>
                <div className="ps-4 pe-3" style={{ flexGrow: 1, width: '60%' }}>
                    <GraphCard />
                </div>
            </div>
        </>

    )
}

// needs to be a flax box thing like the other code I made (wraps underneath)
// needs a line box thing around it

export default PicoDashboard
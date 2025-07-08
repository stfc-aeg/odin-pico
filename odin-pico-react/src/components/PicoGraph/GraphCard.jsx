import LiveView from './Graphs/LiveView';
import CurrentPHA from './Graphs/CurrentPHA';
import UICard from '../utils/UICard';

import { WithEndpoint } from 'odin-react';

const EndpointCheckbox = WithEndpoint((props) => (
  <input type="checkbox" {...props} />
));

const GraphCard = ({ pico_endpoint }) => {

    const canRun = {
        a: pico_endpoint?.data?.device?.settings?.channels?.a?.active,
        b: pico_endpoint?.data?.device?.settings?.channels?.b?.active,
        c: pico_endpoint?.data?.device?.settings?.channels?.c?.active,
        d: pico_endpoint?.data?.device?.settings?.channels?.d?.active,
    };

    return (
        <>
            <UICard title="Live View and PHA Data:">
                <LiveView
                    pico_endpoint={pico_endpoint}
                    EndpointCheckbox={EndpointCheckbox}
                    canRun={canRun}
                />
                {/* <CurrentPHA
                    pico_endpoint={pico_endpoint}
                    EndpointCheckbox={EndpointCheckbox}
                    canRun={canRun}
                /> */}
            </UICard>
        </>
    )
}


export default GraphCard
import UICard from '../../utils/UICard';
import {toSiUnit} from '../../utils/utils';

const GpibTecStatus = ({ pico_endpoint }) => {
    const setPoint = pico_endpoint?.data?.gpib?.info?.tec_setpoint ?? 0;
    const measured = pico_endpoint?.data?.gpib?.info?.tec_temp_meas ?? 0;
    const current = pico_endpoint?.data?.gpib?.info?.tec_current ?? 0;
    const voltage = pico_endpoint?.data?.gpib?.info?.tec_voltage ?? 0;

    return (
        <UICard title="TEC Status">
            <table className="table table-striped mb-0">
                <tbody>
                    <tr>
                        <th>
                            Set-point {setPoint}°C
                        </th>

                        <th>
                            Measured {measured}°C
                        </th>
                    </tr>
                    <tr>
                        <th>
                            Current {toSiUnit(current)}A
                        </th>

                        <th>
                            Voltage {toSiUnit(voltage)}V
                        </th>
                    </tr>
                </tbody>
            </table>
        </UICard>
    )
}

export default GpibTecStatus
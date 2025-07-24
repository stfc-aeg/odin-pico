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
                            Set-point °C
                        </th>

                        <th>
                            {setPoint}
                        </th>
                    </tr>
                    <tr>
                        <th>
                            Measured °C
                        </th>

                        <th>
                            {measured}
                        </th>
                    </tr>
                    <tr>
                        <th>
                            Current
                        </th>

                        <th>
                            {toSiUnit(current)}A
                        </th>
                    </tr>
                    <tr>
                        <th>
                            Voltage V
                        </th>

                        <th>
                            {toSiUnit(voltage)}V
                        </th>
                    </tr>
                </tbody>
            </table>
        </UICard>
    )
}

export default GpibTecStatus
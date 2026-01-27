import { Card, Container, Row, Col, InputGroup } from 'react-bootstrap';
import { OdinTable, OdinTableRow } from 'odin-react';
import ProgressBar from './ProgressBar';
import { ScrollToEnd } from '../../utils/utils';

const CaptureStatus = ({ pico_endpoint, EndpointInput, captureRunning }) => {
  const progressClass = captureRunning ? 'bg-green' : '';
  const fileSettingsPath = pico_endpoint?.data?.device?.settings?.file ?? {};

  const file = fileSettingsPath?.curr_file_name;
  const recorded = fileSettingsPath?.last_write_success ? "True" : "False";
  const available_space = fileSettingsPath?.available_space;
  const trigger_rate = fileSettingsPath?.trigger_rate;
  const max_acq = fileSettingsPath?.max_acq_time
  const max_fw = fileSettingsPath?.max_file_time
  const mean_acq = fileSettingsPath?.mean_acq_time
  const mean_fw = fileSettingsPath?.mean_file_time

  return (
    <Card className="mt-3 border overflow-hidden" style={{ borderRadius: '3px' }}>
      <Card.Header
        className="px-3 py-2 border-bottom fw-semibold"
        style={{ fontSize: '0.85rem', backgroundColor: '#f5f5f5' }}
      >
        Capture Status
      </Card.Header>

      <Card.Body className={`p-0 ${progressClass}`} style={{ fontSize: '14px' }}>
        <Container fluid className="px-3 py-3">
          <Row className="g-3 align-items-center">
            <OdinTable
              className="capture-status-table"
              bordered
              size="sm"
              striped={true}
              columns={{
                filename: "Filename",
                disk: "Disk Space",
                trigger: "Trigger Rate",
                recorded: "Recorded",
              }}
              widths={{
                filename: "50%",
                disk: "19%",
                trigger: "19%",
                recorded: "12%",
              }}
            >
              <OdinTableRow
                row={{
                  filename: (
                    <ScrollToEnd watch={file}>
                      {file || "—"}
                    </ScrollToEnd>
                  ),
                  disk: available_space ?? "—",
                  trigger: trigger_rate ?? "—",
                  recorded,
                }}
              />
            </OdinTable>
          </Row>
          <Row>
            <OdinTable
              bordered
              size="sm"
              striped={true}
              columns={{
                mean_acq: "Mean Acq Time",
                max_acq: "Max Acq Time",
                mean_fw: "Mean File Time",
                max_fw: "Max File Time"
              }}
              widths={{
                mean_acq: "25%",
                max_acq: "25%",
                mean_fw: "25%",
                max_fw: "25%"
              }}
            >
              <OdinTableRow
                row={{
                  mean_acq: mean_acq || "—",
                  max_acq: max_acq || "—",
                  mean_fw: mean_fw || "—",
                  max_fw: max_fw || "—",
                }}
              />
            </OdinTable>
          </Row>
          <Row>
            <Col>
              <ProgressBar response={pico_endpoint?.data} />
            </Col>
          </Row>
        </Container>
      </Card.Body>
    </Card>
  );
};

export default CaptureStatus;

const CaptureControl = ({ pico_endpoint, captureRunning, fileValid }) => {
    const handleButtonClick = (path) => {
        pico_endpoint.put(true, path);
    };

    return (
        <>
            {!captureRunning ? (
                <th className="align-middle">
                    <button
                        className="btn btn-success"
                        onClick={() => handleButtonClick("device/commands/run_user_capture")}
                        disabled={!fileValid}
                    >
                        Start Capture
                    </button>
                </th>
            ) : (
                <th className="align-middle">
                    <button
                        className="btn btn-danger"
                        onClick={() => handleButtonClick("device/flags/abort_cap")}
                        disabled={!fileValid}
                    >
                        Abort Capture
                    </button>
                </th>
            )}
        </>
    )
}

export default CaptureControl

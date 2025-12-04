import React, { useState, useEffect, useRef } from 'react';

const ProgressBar = ({ response }) => {
    const [progress, setProgress] = useState(0);
    const [repeatAmount, setRepeat] = useState(0)
    const [label, setLabel] = useState('Capture Progress');
    const progressTracker = useRef({ highestProgress: 0, lastRepeat: -1, lastSweepIndex: -1, lastKey: "", completedOps: 0 });

    useEffect(() => {
        if (!response) return;

        if (response.device?.gpio?.listening === true) {
            const capturesDone = response.device.gpio.gpio_captures || 0;
            const capturesTarget = response.device.gpio.capture_run || 1;


            const percent = Math.min(100, (capturesDone / capturesTarget) * 100);


            setProgress(percent);
            setRepeat(`${capturesDone}/${capturesTarget}`);
            setLabel(`GPIO Capture Progress`);
            return;
        }

        if (response.device?.commands?.run_user_capture === true || response.device?.gpio?.listening === true) {
            // Progress calculation logic
            const isRepeatingEnabled = response.device.settings.capture.capture_repeat === true;
            const repeatAmount = isRepeatingEnabled ? (response.device.settings.capture.repeat_amount || 1) : 1;
            const currentRepeat = isRepeatingEnabled ? (response.device.live_view.current_capture || 0) : 0;
            const isGpibControlEnabled = response.gpib?.gpib_control === true;
            const isTempSweepActive = response.gpib?.temp_sweep?.active === true;
            const isTempSweepEffective = isGpibControlEnabled && isTempSweepActive;
            const sweepTotal = isTempSweepEffective ? (response.device.live_view.sweep_total || 1) : 1;
            const sweepIndex = isTempSweepEffective ? (response.device.live_view.sweep_index || 0) : 0;
            const isCaptureTimeBased = response.device.settings.capture.capture_mode === true;
            const captureTime = response.device.settings.capture.capture_time || 1;
            const currentTbdcTime = response.device.live_view.current_tbdc_time || 0;
            const captureCount = response.device.live_view.capture_count || 0;
            const capturesRequested = response.device.live_view.captures_requested || 1;

            const totalOperations = repeatAmount * sweepTotal;

            const state = progressTracker.current;
            const currentKey = `${currentRepeat}-${sweepIndex}`;

            if (state.lastKey !== "" && currentKey !== state.lastKey) {
                state.completedOps++;
            }

            const currentCombinationProgress = isCaptureTimeBased
                ? currentTbdcTime / captureTime
                : captureCount / capturesRequested;

            const combinationWeight = 100 / totalOperations;
            const completedProgress = state.completedOps * combinationWeight;
            const currentProgress = Math.min(1, Math.max(0, currentCombinationProgress)) * combinationWeight;
            const totalProgress = Math.min(100, Math.max(state.highestProgress, completedProgress + currentProgress));

            state.highestProgress = totalProgress;
            state.lastKey = currentKey;
            state.lastRepeat = currentRepeat;
            state.lastSweepIndex = sweepIndex;

            if (response.device?.gpio?.listening === true) {
                setProgress(progress + (totalProgress / response.device.gpio.capture_run))
            } else {
                setProgress(totalProgress);
                setRepeat(`${currentRepeat + 1}/${repeatAmount}`);

                let statusText = "";
                if (isRepeatingEnabled) {
                    statusText += `Repeat ${currentRepeat + 1}/${repeatAmount}`;
                }
                if (isTempSweepEffective) {
                    if (statusText) statusText += ", ";
                    statusText += `Temp ${sweepIndex + 1}/${sweepTotal}`;
                }
                setLabel(statusText ? `Capture Progress: ${statusText}` : 'Capture Progress');
            }

        } else {
            setProgress(0);
            setLabel('Capture Progress');
            progressTracker.current = { highestProgress: 0, lastRepeat: -1, lastSweepIndex: -1, lastKey: "", completedOps: 0 };
        }
    }, [response]);

    return (
        <>
            <div style={{ fontSize: '14px' }}>{label}</div>
            <div className="progress mt-2">
                <div
                    id="capture-progress-bar"
                    className="progress-bar"
                    role="progressbar"
                    style={{ width: `${progress}%` }}
                    aria-valuenow={progress}
                    aria-valuemin="0"
                    aria-valuemax="100"
                >
                    {progress.toFixed(1)}%  ({repeatAmount})
                </div>
            </div>
        </>
    );
};

export default ProgressBar;

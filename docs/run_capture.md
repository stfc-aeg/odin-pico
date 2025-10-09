# PicoController.run_capture() - Function Overview

## Purpose

The `run_capture()` function is the central orchestration method in PicoController. It manages the complete lifecycle of data acquisition, handling different capture modes, temperature control integration, file writing, and capture repetition. This function is called repeatedly by the `update_loop()` executor thread at 200ms intervals.

## High-Level Overview

The function operates in two primary modes:

1. **User Capture Mode**: Triggered when the user requests a capture, collects data and saves to file
2. **Live View Mode**: Runs continuously in the background, collecting data for real-time display without saving

Within User Capture Mode, the capture strategy is determined by multiple configuration options that can be combined:

### Capture Type
- **Fixed-Count Capture** (`capture_type = 0`): Collect a specific number of waveforms (`n_captures`)
- **Time-Based Capture** (`capture_type = 1`): Collect data for a specified duration (`capture_time` in seconds)

### Temperature Control (Optional, requires GPIB, Refer to GPIB_integration.md)
- **No Temperature Control**: Capture without considering temperature
- **Single-Shot Temperature**: Set one target temperature, wait for stability, then capture
- **Temperature Sweep**: Automatically step through multiple temperature points, waiting for stability, capturing at each

### Repetition (Optional)
- **Single Run**: Execute the capture once
- **Repeated Capture**: Run the entire capture sequence multiple times with configurable delays between runs

### Valid Combinations

These options combine to create various workflows:

| Capture Type | Temperature Control | Repetition | Result |
|--------------|---------------------|------------|--------|
| Fixed-Count | None | Single | 100 waveforms at current temperature |
| Fixed-Count | Single-Shot (25°C) | Single | 100 waveforms after stabilising at 25°C |
| Fixed-Count | Sweep (20-30°C) | Single | 100 waveforms at 20°C, 100 at 25°C, 100 at 30°C (3 files) |
| Time-Based | None | Single | 60 seconds of data at current temperature |
| Time-Based | Single-Shot (25°C) | Single | 60 seconds of data after stabilising at 25°C |
| Time-Based | Sweep (20-30°C) | Single | 60 seconds at 20°C, 60s at 25°C, 60s at 30°C (3 files) |
| Fixed-Count | None | Repeated (3x) | 100 waveforms, 3 times with delays (3 files: `_1`, `_2`, `_3`) |
| Fixed-Count | Sweep (20-30°C) | Repeated (2x) | Full temperature sweep twice (6 files total) |
| Time-Based | Single-Shot (25°C) | Repeated (5x) | 60 seconds at 25°C, repeated 5 times (5 files) |

**Note**: The filename is constructed in the order: `<base><temp_suffix><repeat_suffix>.hdf5`

When temperature sweep is combined with repetition, the entire sweep is repeated. For example, with a base filename `capture`, a 20-30°C sweep (3 points) repeated 2 times, you get:

- Run 1: `capture_20-0c_1.hdf5`, `capture_25-0c_1.hdf5`, `capture_30-0c_1.hdf5`
- Run 2: `capture_20-0c_2.hdf5`, `capture_25-0c_2.hdf5`, `capture_30-0c_2.hdf5`

(Total: 6 files)

## Detailed Step-by-Step Breakdown

### 1. Single-Shot Temperature Wait

If user set a target temperature via `/gpib/set/set_temp`, block here until TEC stabilises. A background thread handles the actual temperature setting and polling.

### 2. Initialise Capture

Reset abort flag, clear temperature flags, calculate sampling time, optionally verify settings.

### 3. Branch: User Capture or Live View?

- **User Capture**: Steps 4-9 below
- **Live View**: Skip to step 10

---

## User Capture Mode (Steps 4-9)

### 4. Validate Filename

Check filename is valid and doesn't exist. If invalid, abort and show error.

### 5. Setup Repetition

Determine how many times to run (`cap_loop`) and delay between runs based on `capture_repeat` settings.

### 6. Main Loop - For Each Repetition

For each iteration:
- Add repeat suffix to filename (e.g., `_1`, `_2`)
- Reset abort flag and PHA data
- Execute capture based on mode (step 7)
- Wait for delay if not final iteration (step 8)

### 7. Execute Capture

Four possible paths based on capture type and GPIB settings:

| Capture Type | GPIB Active? | Action |
|--------------|--------------|--------|
| Fixed-Count | No | `user_capture(True)` - collect `n_captures` waveforms |
| Fixed-Count | Yes | `run_temperature_sweep()` → `user_capture(True)` at each temp |
| Time-Based | No | `tb_capture()` - collect for `capture_time` seconds |
| Time-Based | Yes | `run_temperature_sweep()` → `tb_capture()` at each temp |


### 8. Inter-Capture Delay

If not the final repetition, wait for `capture_delay` seconds (abortable).

### 9. Cleanup

After all repetitions complete, reset all flags and tracking variables, clear filename suffixes.

---

## Live View Mode (Step 10)

### 10. Background Live View

When no user capture is active, continuously collect 2 waveforms for UI display via `user_capture(False)`. No file saving. 2 captures are completed due to the trigger_timing data returned having the first trigger_timing as 0 due to it being the first capture in that sequence. The trigger timings are used to help estimate how long the system can for when running in time based mode. 

---


"""
This will set the PWM of a single module (specified by MODULE_X, MODULE_Y) to 20%
and show and record the RPMs

warmup time of 5 seconds and 10 seconds measuring, it will show us
- Live CLI table showing RPMs for all fans
- The mean RPM of each fan
- The median RPM
- Standard deviation
- min, max
- p99, p75, p5, p10

And will plot the RPMs of each fan over time
"""

import os
import sys
import time
from collections import defaultdict
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from windsuite_sdk import ModuleInfo, WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="localhost")

MODULE_X = 2
MODULE_Y = 2
PWM_PERCENT = 20
WARMUP_TIME_S = 20
MEASURE_TIME_S = 120

# Data storage: {(position, layer_name, fan_index): [(timestamp, rpm), ...]}
rpm_data: dict[tuple[tuple[int, int], str, int], list[tuple[float, float]]] = (
    defaultdict(list)
)
# Live RPM storage: {(position, layer_name): [rpm for each fan]}
live_rpms: dict[tuple[tuple[int, int], str], list[float]] = {}
recording = False
start_time = 0.0


def display_live_rpms() -> None:
    """Display live RPM values for the target module as a table."""
    if not live_rpms:
        return

    # Clear screen and move cursor to top
    sys.stdout.write("\033[2J\033[H")

    elapsed = time.time() - start_time if start_time else 0
    print(
        f"LIVE RPM MONITOR | Module ({MODULE_X}, {MODULE_Y}) | Elapsed: {elapsed:.1f}s | PWM: {PWM_PERCENT}%"
    )
    print()

    position = (MODULE_X, MODULE_Y)

    # Header row with fan indices
    downstream = live_rpms.get((position, "DOWNSTREAM"), [])
    num_fans = len(downstream) if downstream else 9
    header = "            " + "".join(f"{i:>7}" for i in range(num_fans))
    print(header)

    # Downstream row
    if downstream:
        row = "DOWNSTREAM  " + "".join(f"{rpm:>7.0f}" for rpm in downstream)
        print(row)

    # Upstream row
    upstream = live_rpms.get((position, "UPSTREAM"), [])
    if upstream:
        row = "UPSTREAM    " + "".join(f"{rpm:>7.0f}" for rpm in upstream)
        print(row)

    sys.stdout.flush()


def on_module_update(data: dict[tuple[int, int], ModuleInfo]) -> None:
    """Callback for module updates - records RPM data when recording is enabled."""
    global recording, start_time

    if not recording:
        return

    target_position = (MODULE_X, MODULE_Y)
    if target_position not in data:
        return

    current_time = time.time() - start_time
    module_info = data[target_position]

    for layer_index in range(len(module_info.current_rpm)):
        layer_name = (
            "DOWNSTREAM" if layer_index == ModuleInfo.INDEX_DOWNSTREAM else "UPSTREAM"
        )

        # Store for live display
        live_rpms[(target_position, layer_name)] = list(
            module_info.current_rpm[layer_index]
        )

        for fan_index in range(len(module_info.current_rpm[layer_index])):
            current_rpm = module_info.current_rpm[layer_index][fan_index]
            key = (target_position, layer_name, fan_index)
            rpm_data[key].append((current_time, current_rpm))

    # Update live display
    display_live_rpms()


def calculate_statistics(values: list[float]) -> dict[str, np.floating[Any]]:
    """Calculate statistics for a list of RPM values."""
    arr = np.array(values)
    return {
        "mean": np.mean(arr),
        "median": np.median(arr),
        "std": np.std(arr),
        "min": np.min(arr),
        "max": np.max(arr),
        "p99": np.percentile(arr, 99),
        "p75": np.percentile(arr, 75),
        "p10": np.percentile(arr, 10),
        "p5": np.percentile(arr, 5),
    }


def print_statistics() -> None:
    """Print statistics for all recorded fans."""
    print("\n" + "=" * 60)
    print("RPM STATISTICS")
    print("=" * 60)

    for key, data in sorted(rpm_data.items()):
        position, layer_name, fan_index = key
        rpms = [rpm for _, rpm in data]

        if not rpms:
            continue

        stats = calculate_statistics(rpms)

        print(f"\nModule {position} - {layer_name} - Fan {fan_index}:")
        print(f"  Mean:   {stats['mean']:.2f} RPM")
        print(f"  Median: {stats['median']:.2f} RPM")
        print(f"  Std:    {stats['std']:.2f} RPM")
        print(f"  Min:    {stats['min']:.2f}RPM")
        print(f"  Max:    {stats['max']:.2f}RPM")
        print(f"  p99:    {stats['p99']:.2f} RPM")
        print(f"  p75:    {stats['p75']:.2f} RPM")
        print(f"  p10:    {stats['p10']:.2f} RPM")
        print(f"  p5:     {stats['p5']:.2f} RPM")


def plot_rpm_data() -> None:
    """Plot RPM data for all fans over time."""
    if not rpm_data:
        print("No data to plot")
        return

    # Group by position and layer for subplots
    positions = sorted(set(key[0] for key in rpm_data.keys()))
    layers = ["DOWNSTREAM", "UPSTREAM"]

    fig, axes = plt.subplots(
        len(positions), len(layers), figsize=(14, 5 * len(positions)), squeeze=False
    )

    fig.suptitle(f"Fan RPM over time (PWM={PWM_PERCENT}%)", fontsize=14)

    for pos_idx, position in enumerate(positions):
        for layer_idx, layer_name in enumerate(layers):
            ax = axes[pos_idx, layer_idx]
            ax.set_title(f"Module {position} - {layer_name}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("RPM")
            ax.grid(True, alpha=0.3)

            for fan_index in range(9):  # 9 fans per layer
                key = (position, layer_name, fan_index)
                if key in rpm_data and rpm_data[key]:
                    times = [t for t, _ in rpm_data[key]]
                    rpms = [rpm for _, rpm in rpm_data[key]]
                    ax.plot(times, rpms, label=f"Fan {fan_index}", alpha=0.7)

            ax.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig("rpm_plot.png", dpi=150)
    print("\nPlot saved to rpm_plot.png")
    plt.show()


def main() -> None:
    """Main function to run the fan test."""
    global recording, start_time

    base_url = f"http://{SERVER_IP_ADDRESS}"
    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.register_module_update_callback(callback=on_module_update)
    sdk.start_communication()

    try:
        # Set PWM to target percentage
        print(f"\nSetting PWM to {PWM_PERCENT}%...")
        sdk.fan_controller.row(MODULE_Y).column(MODULE_X).set_intensity(
            percent=PWM_PERCENT
        ).apply()

        # Warmup phase
        print(f"Warming up for {WARMUP_TIME_S} seconds...")
        time.sleep(WARMUP_TIME_S)

        # Measurement phase
        print(f"Recording RPM data for {MEASURE_TIME_S} seconds...")
        recording = True
        start_time = time.time()
        time.sleep(MEASURE_TIME_S)
        recording = False

        print("Recording complete!")

        # Print statistics
        print_statistics()
        sdk.fan_controller.set_intensity(0).apply()

        # Plot the data
        plot_rpm_data()

    except KeyboardInterrupt:
        print("\nInterrupted by user...")
    finally:
        print("\nShutting down - setting fans to 0%...")
        sdk.fan_controller.set_intensity(0).apply()
        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

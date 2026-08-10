# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib>=3.10.8",
#     "numpy>=2.4.6",
#     "windsuite-sdk>=0.5.0",
# ]
# ///
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
from windsuite_sdk import ModuleInfo, WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")

MODULE_X = 1
MODULE_Y = 1
PWM_PERCENT = 5
WARMUP_TIME_S = 5
MEASURE_TIME_S = 20

# Data storage: {(position, layer_name, fan_index): [(timestamp, rpm), ...]}
rpm_data: dict[tuple[tuple[int, int], str, int], list[tuple[float, float]]] = (
    defaultdict(list)
)
# Live RPM storage: {(position, layer_name): [rpm for each fan]}
live_rpms: dict[tuple[tuple[int, int], str], list[float]] = {}
recording = False
start_time = 0.0


# ANSI color codes
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


def format_rpm_with_color(rpm: float, upstream: bool) -> str:
    """Format RPM value with color based on whether it's in expected range."""
    upper, lower, _ = rpm_range_from_pwm(PWM_PERCENT, upstream)
    if lower <= rpm <= upper:
        return f"{COLOR_GREEN}{rpm:>7.0f}{COLOR_RESET}"
    else:
        return f"{COLOR_RED}{rpm:>7.0f}{COLOR_RESET}"


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
        row = "DOWNSTREAM  " + "".join(
            format_rpm_with_color(rpm, upstream=False) for rpm in downstream
        )
        print(row)

    # Upstream row
    upstream = live_rpms.get((position, "UPSTREAM"), [])
    if upstream:
        row = "UPSTREAM    " + "".join(
            format_rpm_with_color(rpm, upstream=True) for rpm in upstream
        )
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


def rpm_range_from_pwm(
    pwm_percent: int,
    upstream: bool,
    accuracy_range: float = 0.10,
) -> tuple[int, int, int]:
    """
    Return expected RPM range for a given PWM power level.

    Args:
        pwm_percent: Power of the fan as percentage (0 to 100)
        upstream: True for upstream layer, False for downstream
        accuracy_range: Acceptable RPM deviation as a fraction (default 10%)

    Returns:
        Tuple of (upper_bound, lower_bound, expected_rpm)
    """
    ax_upstream = 129.5
    b_upstream = 778.6

    ax_downstream = 124.9
    b_downstream = 717.4

    if pwm_percent < 10:
        return (0, 0, 0)

    pwm_percent = min(pwm_percent, 100)
    if upstream:
        rpm = ax_upstream * pwm_percent + b_upstream
    else:
        rpm = ax_downstream * pwm_percent + b_downstream

    upper = rpm + rpm * accuracy_range
    lower = rpm - rpm * accuracy_range

    return (int(upper), int(lower), int(rpm))


def check_rpm_in_range(
    mean_rpm: float, layer_name: str, pwm_percent: int, accuracy_range: float = 0.10
) -> tuple[bool, int, int, int]:
    """
    Check if the measured mean RPM is within the expected range.

    Args:
        mean_rpm: The measured mean RPM value
        layer_name: "UPSTREAM" or "DOWNSTREAM"
        pwm_percent: The PWM percentage (0-100)
        accuracy_range: Acceptable RPM deviation as a fraction

    Returns:
        Tuple of (is_in_range, upper_bound, lower_bound, expected_rpm)
    """
    upstream = layer_name == "UPSTREAM"
    upper, lower, expected = rpm_range_from_pwm(pwm_percent, upstream, accuracy_range)

    is_in_range = lower <= mean_rpm <= upper
    return (is_in_range, upper, lower, expected)


def print_statistics() -> None:
    """Print statistics for all recorded fans."""
    print("\n" + "=" * 60)
    print("RPM STATISTICS")
    print("=" * 60)

    failed_fans: list[tuple[tuple[int, int], str, int, float, int, int]] = []

    for key, data in sorted(rpm_data.items()):
        position, layer_name, fan_index = key
        rpms = [rpm for _, rpm in data]

        if not rpms:
            continue

        stats = calculate_statistics(rpms)
        mean_rpm = float(stats["mean"])

        # Check if RPM is within expected range
        in_range, upper, lower, expected = check_rpm_in_range(
            mean_rpm, layer_name, PWM_PERCENT
        )
        status = "OK" if in_range else "FAIL"

        print(f"\nModule {position} - {layer_name} - Fan {fan_index}: [{status}]")
        print(
            f"  Mean:     {mean_rpm:.2f} RPM (expected: {expected}, range: {lower}-{upper})"
        )
        print(f"  Median:   {stats['median']:.2f} RPM")
        print(f"  Std:      {stats['std']:.2f} RPM")
        print(f"  Min:      {stats['min']:.2f} RPM")
        print(f"  Max:      {stats['max']:.2f} RPM")
        print(f"  p99:      {stats['p99']:.2f} RPM")
        print(f"  p75:      {stats['p75']:.2f} RPM")
        print(f"  p10:      {stats['p10']:.2f} RPM")
        print(f"  p5:       {stats['p5']:.2f} RPM")

        if not in_range:
            failed_fans.append(
                (position, layer_name, fan_index, mean_rpm, lower, upper)
            )

    # Print summary
    print("\n" + "=" * 60)
    print("RPM RANGE CHECK SUMMARY")
    print("=" * 60)
    total_fans = len(rpm_data)
    passed_fans = total_fans - len(failed_fans)
    print(f"Passed: {passed_fans}/{total_fans}")

    if failed_fans:
        print("\nFailed fans:")
        for position, layer_name, fan_index, mean_rpm, lower, upper in failed_fans:
            print(
                f"  Module {position} - {layer_name} - Fan {fan_index}: "
                f"{mean_rpm:.2f} RPM (expected range: {lower}-{upper})"
            )


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

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy>=2.4.6",
#     "rerun-sdk>=0.28.2",
#     "windsuite-sdk>=0.5.0",
# ]
# ///
"""Live plot wind probe velocity data using Rerun.

Connects to WindSuite SDK and visualizes wind velocities in real-time.
"""

import os
import threading
import time

import numpy as np
import rerun as rr
import rerun.blueprint as rrb
from windsuite_sdk import WindProbeData, WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")
TIME_WINDOW_SECONDS = 10.0


def clean_value(value: float) -> float:
    """Replace values lower than -900 with NaN."""
    if value < -900:
        return np.nan
    return value


def on_windprobe_data(data: WindProbeData) -> None:
    """
    Callback for wind probe data - logs velocities to Rerun.

    Args:
        data: Wind probe measurements including velocity, temperature, and pressure.
    """
    current_time = time.time()
    rr.set_time("time", timestamp=current_time)

    # Wind velocity in probe reference frame
    x_probe = data.wind_velocity_mps_probe_ref.x
    y_probe = data.wind_velocity_mps_probe_ref.y
    z_probe = data.wind_velocity_mps_probe_ref.z
    mag_probe = np.sqrt(x_probe**2 + y_probe**2 + z_probe**2)

    rr.log("velocities/probe_ref/x", rr.Scalars(x_probe))
    rr.log("velocities/probe_ref/y", rr.Scalars(y_probe))
    rr.log("velocities/probe_ref/z", rr.Scalars(z_probe))
    rr.log("velocities/probe_ref/magnitude", rr.Scalars(mag_probe))

    # Wind velocity in windshaper reference frame
    x_ws = data.wind_velocity_mps_windshaper_ref.x
    y_ws = data.wind_velocity_mps_windshaper_ref.y
    z_ws = data.wind_velocity_mps_windshaper_ref.z
    mag_ws = np.sqrt(x_ws**2 + y_ws**2 + z_ws**2)

    rr.log("velocities/windshaper_ref/x", rr.Scalars(x_ws))
    rr.log("velocities/windshaper_ref/y", rr.Scalars(y_ws))
    rr.log("velocities/windshaper_ref/z", rr.Scalars(z_ws))
    rr.log("velocities/windshaper_ref/magnitude", rr.Scalars(mag_ws))


def create_blueprint() -> rrb.Blueprint:
    """
    Create a blueprint with wind velocity views
    This sets up the rerun visualization layout.
    """
    time_range = [
        rrb.VisibleTimeRange(
            "time",
            start=rrb.TimeRangeBoundary.cursor_relative(seconds=-TIME_WINDOW_SECONDS),
            end=rrb.TimeRangeBoundary.cursor_relative(seconds=0),
        ),
    ]

    blueprint = rrb.Blueprint(
        rrb.Vertical(
            rrb.TimeSeriesView(
                name="Wind Velocity (Probe Reference)",
                origin="/velocities/probe_ref",
                time_ranges=time_range,
                plot_legend=rrb.PlotLegend(visible=True),
            ),
            rrb.TimeSeriesView(
                name="Wind Velocity (Windshaper Reference)",
                origin="/velocities/windshaper_ref",
                time_ranges=time_range,
                plot_legend=rrb.PlotLegend(visible=True),
            ),
        ),
        collapse_panels=False,
    )

    return blueprint


stop_event = threading.Event()


def main() -> None:
    """Main function to run the WindSuite SDK with Rerun visualization."""
    base_url = f"http://{SERVER_IP_ADDRESS}"

    rr.init("windprobe_velocities", spawn=True)
    print("Rerun viewer initialized")

    blueprint = create_blueprint()
    rr.send_blueprint(blueprint, make_active=True, make_default=False)
    print(f"Blueprint configured with {TIME_WINDOW_SECONDS}s time window")
    time.sleep(0.1)

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    sdk.register_windprobe_callback(callback=on_windprobe_data)
    sdk.start_communication()

    print("Listening for wind probe data. Press Ctrl+C to stop...")

    try:
        while not stop_event.wait(timeout=0.1):
            pass

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_event.set()
    finally:
        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

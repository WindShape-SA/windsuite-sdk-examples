# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy>=2.4.6",
#     "windsuite-sdk>=0.5.0",
# ]
# ///
import os
import threading

import numpy as np
from windsuite_sdk import TrackedProbeData, WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")
TIME_WINDOW_SECONDS = 10.0


def on_tracked_probe_data(data: TrackedProbeData) -> None:
    """
    Callback for wind probe data
    """

    x_probe = data.wind_velocity_mps.x
    y_probe = data.wind_velocity_mps.y
    z_probe = data.wind_velocity_mps.z
    mag_probe = np.sqrt(x_probe**2 + y_probe**2 + z_probe**2)

    x_position = data.position_data_mm.x
    y_position = data.position_data_mm.y
    z_position = data.position_data_mm.z

    print(
        f"Received data - Velocity (m/s): ({x_probe:.2f}, {y_probe:.2f}, {z_probe:.2f}), Magnitude: {mag_probe:.2f}"
    )
    print(f"Position (mm): ({x_position:.1f}, {y_position:.1f}, {z_position:.1f})")


stop_event = threading.Event()


def main() -> None:
    """Main function to run the WindSuite SDK with Rerun visualization."""
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    sdk.register_tracked_probe_callback(callback=on_tracked_probe_data)
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


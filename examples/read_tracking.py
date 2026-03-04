import os
import threading

from dotenv import load_dotenv
from windsuite_sdk import TrackingData, WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")


def on_tracking_data(data: dict[str, TrackingData]) -> None:
    """
    Callback for tracking data.

    Args:
        data: Dictionary mapping object names to their tracking data.

    """
    print(f"=== Tracking Data ({len(data)} objects) ===")

    for object_name, tracking_data in data.items():
        print(f"Object: {object_name}")
        print(f"  Timestamp: {tracking_data.timestamp}s")

        # Position
        pos = tracking_data.position_meters_world_ref
        print(f"  Position (world): ({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}) m")

        # Rotation (quaternion)
        rot = tracking_data.rotation_world_ref
        print(
            f"  Rotation (world): w={rot.w:.3f}, x={rot.x:.3f}, y={rot.y:.3f}, z={rot.z:.3f}"
        )

        vel = tracking_data.velocity_mps_world_ref
        print(f"  Velocity (world): (X:{vel.x:.2f}, Y:{vel.y:.2f}, Z:{vel.z:.2f}) m/s")

        rot_speed_degps = tracking_data.angular_velocity_degps_world_ref
        print(
            f"  Angular Velocity (world): (X:{rot_speed_degps.x:.2f}, Y:{rot_speed_degps.y:.2f}, Z:{rot_speed_degps.z:.2f}) deg/s"
        )

    print()


stop_event = threading.Event()


def main() -> None:
    """Main function to run the WindSuite SDK example."""
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    sdk.register_tracking_callback(callback=on_tracking_data)

    sdk.start_communication()

    try:
        freq_hz = 25

        while not stop_event.wait(timeout=(1.0 / freq_hz)):
            # ! DO WHATEVER
            pass

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_event.set()
    finally:
        sdk.fan_controller.set_intensity(0).apply()

        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

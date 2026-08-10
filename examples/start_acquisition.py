import os
import threading

from windsuite_sdk import WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")

stop_event = threading.Event()


def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.start_communication()

    try:
        success = sdk.start_acquisition(name="test-001")
        if success:
            print("Acquisition started successfully.")
        else:
            print("Failed to start acquisition.")
            stop_event.set()

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_event.set()
    finally:
        sdk.fan_controller.set_intensity(0).apply()
        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

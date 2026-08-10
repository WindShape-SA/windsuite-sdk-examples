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
        sdk.set_psu(state=True)
        stop_event.wait(timeout=2)

        sdk.fan_controller.even_modules().fans(fans=[1, 3, 5, 7, 9]).set_intensity(
            percent=20
        )
        sdk.fan_controller.odd_modules().fans(fans=[2, 4, 6, 8]).set_intensity(
            percent=80
        )
        sdk.fan_controller.apply()

        stop_event.wait(timeout=10)

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_event.set()
    finally:
        sdk.fan_controller.set_intensity(0).apply()
        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

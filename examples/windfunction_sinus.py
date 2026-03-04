import os
import threading
from math import pi, sin

from dotenv import load_dotenv
from windsuite_sdk import WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")

stop_event = threading.Event()


def windfunction(x_pos: float, y_pos: float, time: float) -> float:
    """
    Args:
        x_pos (float): The x-coordinate of the fan's position, normalized to the range [0.0 - 1.0].
        y_pos (float): The y-coordinate of the fan's position, normalized to the range [0.0 - 1.0].
        time (float): The current time in seconds.
    Returns:
        float: The calculated wind intensity [0.0 - 100.0] for the given position.
    """

    intensity = 0.5 + 0.2 * sin(2 * pi * 2 * (y_pos - x_pos) + time)

    return intensity * 100


def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.start_communication()

    main_loop_hz = 20

    try:
        sdk.set_psu(state=True)
        stop_event.wait(timeout=2)

        while not stop_event.wait(timeout=(1.0 / main_loop_hz)):
            sdk.fan_controller.set_intensity_function(windfunction).apply()
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

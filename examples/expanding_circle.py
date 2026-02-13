import os
import threading
from math import sin

from dotenv import load_dotenv
from windsuite_sdk import WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="localhost")

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
    center_x = 0.5
    center_y = 0.5
    base_radius = 0.3
    radius_variation = 0.3

    current_radius = base_radius + (sin(time * 3) * radius_variation)

    distance = ((x_pos - center_x) ** 2 + (y_pos - center_y) ** 2) ** 0.5
    max_distance = (2 * (current_radius**2)) ** 0.5
    intensity = max(0.0, min(100.0, (1 - (distance / max_distance)) * 100))
    return intensity


def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.start_communication()

    main_loop_hz = 40

    try:
        sdk.set_psu(state=True)
        stop_event.wait(timeout=2)

        # The SDK will call the provided windfunction with every selected fan's position to determine the intensity in real-time
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

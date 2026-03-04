import os
import threading
from math import atan2, sin

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
    dx = x_pos - 0.5
    dy = y_pos - 0.5
    distance = (dx**2 + dy**2) ** 0.5
    angle = atan2(dy, dx)

    # Rotating vortex: spiral arm that sweeps around the center over time.
    # spiral_tightness controls how many radians of phase shift per unit of distance.
    # rotation_speed controls how fast (rad/s) the vortex rotates.
    spiral_tightness = 8.0
    rotation_speed = 1.5

    phase = angle - spiral_tightness * distance - rotation_speed * time

    intensity = 50.0 + 50.0 * sin(phase)
    return max(0.0, min(40.0, intensity))


def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.start_communication()

    main_loop_hz = 25

    try:
        sdk.set_psu(state=True)
        # stop_event.wait(timeout=2)

        while not stop_event.wait(timeout=(1.0 / main_loop_hz)):
            sdk.fan_controller.set_intensity_function(
                windfunction
            ).apply()

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

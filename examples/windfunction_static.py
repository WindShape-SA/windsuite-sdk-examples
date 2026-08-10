import os
import threading

from windsuite_sdk import WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")

stop_event = threading.Event()


def windfunction(x_pos: float, y_pos: float, time: float) -> float:
    """
    Args:
        x_pos (float): The x-coordinate of the fan's position, normalized to the range [0.0 - 1.0].
        y_pos (float): The y-coordinate of the fan's position, normalized to the range [0.0 - 1.0].
    Returns:
        float: The calculated wind intensity [0.0 - 100.0] for the given position.

    NOTE: Just ignoring and not using time
    """
    base_center_x = 0.5
    base_center_y = 0.5
    radius = 0.4

    center_x = base_center_x
    center_y = base_center_y

    distance = ((x_pos - center_x) ** 2 + (y_pos - center_y) ** 2) ** 0.5
    max_distance = (2 * (radius**2)) ** 0.5
    intensity = max(0.0, min(100.0, (1 - (distance / max_distance)) * 100))
    return intensity


def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.start_communication()

    main_loop_hz = 25

    try:
        sdk.set_psu(state=True)
        stop_event.wait(timeout=2)

        sdk.fan_controller.set_intensity_function(windfunction).apply()

        while not stop_event.wait(timeout=(1.0 / main_loop_hz)):
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

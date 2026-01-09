import math
import os
import threading
import time

from dotenv import load_dotenv
from windsuite_sdk import WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="localhost")

stop_event = threading.Event()

def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)
    sdk.start_communication()

    main_loop_hz = 25
    sinus_freq_hz = 2

    try:

        while not stop_event.wait(timeout=(1.0 / main_loop_hz)):
            # ! SINUS MODULE CHECKERBOARD EXAMPLE
            intensity = 50 + 50 * math.sin(2 * math.pi * sinus_freq_hz * time.time())
            sdk.fan_controller.even_modules().set_intensity(percent=intensity)
            sdk.fan_controller.apply()

    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_event.set()
    finally:
        sdk.fan_controller.set_intensity(0).apply()
        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

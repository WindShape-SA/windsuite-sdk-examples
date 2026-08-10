import os
import threading
import time

from windsuite_sdk import WindProbeData, WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")


def on_windprobe_data(data: WindProbeData) -> None:
    """
    Callback for wind probe data.

    Args:
        data: Wind probe measurements including velocity, temperature, and pressure.

    """
    print("=== Wind Probe Data ===")
    print(f"Timestamp: {data.timestamp_s}s")
    print(
        f"Wind Velocity (probe ref): ({data.wind_velocity_mps_probe_ref.x:.2f}, "
        f"{data.wind_velocity_mps_probe_ref.y:.2f}, "
        f"{data.wind_velocity_mps_probe_ref.z:.2f}) m/s"
    )

    print(f"Temperature: {data.temperature_celcius:.2f}°C")
    print(f"Atmospheric Pressure: {data.atmospheric_pressure_hpascal:.2f} hPa")
    print(f"Static Pressure: {data.static_pressure_pascal:.2f} Pa")
    print()


stop_event = threading.Event()


def main() -> None:
    """Main function to run the WindSuite SDK example."""
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    sdk.register_windprobe_callback(callback=on_windprobe_data)
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
        ret = sdk.fan_controller.set_intensity(0).apply()
        print(ret)
        time.sleep(1)

        sdk.cleanup()
        print("SDK stopped")


if __name__ == "__main__":
    main()

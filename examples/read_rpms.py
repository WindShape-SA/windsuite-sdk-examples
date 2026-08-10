import os
import threading

from windsuite_sdk import ModuleInfo, WindsuiteSDK

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")


def on_module_update(data: dict[tuple[int, int], ModuleInfo]) -> None:
    """
    Callback for module updates.

    Args:
        data: Dictionary mapping module row and column to their information.


    """

    for position, module_info in data.items():
        print(f"Module Position: {position}")
        print(f"  IP Address: {module_info.ip}")
        print(f"  Type: {module_info.type}")
        print(f"  Lifepoints: {module_info.lifepoints}")

        # ! FOR EACH FAN LAYER
        # The fans are indexed as a 3x3 matrix as they are physically arranged in the modules
        # ┌─────┬─────┬─────┐
        # │  1  │  2  │  3  │
        # ├─────┼─────┼─────┤
        # │  4  │  5  │  6  │
        # ├─────┼─────┼─────┤
        # │  7  │  8  │  9  │
        # └─────┴─────┴─────┘

        for layer_index in range(len(module_info.target_pwm)):
            layer_name = (
                "DOWNSTREAM"
                if layer_index == ModuleInfo.INDEX_DOWNSTREAM
                else "UPSTREAM"
            )
            print(f"\tLayer {layer_name}:")

            # ! FOR EACH FAN IN THE LAYER
            for fan_index in range(len(module_info.target_pwm[layer_index])):
                target_pwm = module_info.target_pwm[layer_index][fan_index]
                current_pwm = module_info.current_pwm[layer_index][fan_index]
                current_rpm = module_info.current_rpm[layer_index][fan_index]

                print(
                    f"\t\tFan {fan_index}: Target PWM: {target_pwm:.2f} | Current PWM: {current_pwm:.2f} | Current RPM: {current_rpm:.2f}"
                )

    print("-" * 20)


stop_event = threading.Event()


def main() -> None:
    """Main function to run the WindSuite SDK example."""
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    sdk.register_module_update_callback(callback=on_module_update)

    sdk.start_communication()

    try:
        sdk.set_psu(state=True)
        stop_event.wait(timeout=2)

        sdk.fan_controller.set_intensity(percent=30)
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

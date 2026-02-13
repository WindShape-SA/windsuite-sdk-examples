import os
import threading

from dotenv import load_dotenv
from windsuite_sdk import ModuleInfo, WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="localhost")


def on_module_update(data: dict[tuple[int, int], ModuleInfo]) -> None:
    """
    Callback for module updates.

    Args:
        data: Dictionary mapping module row and column to their information.


    """

    for position, module_info in data.items():
        print("-" * 20)
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
        esc_rpm: int | None = module_info.esc_rpm
        applied_pwm_us: int | None = module_info.applied_pwm_us
        esc_voltage_mv: int | None = module_info.esc_voltage_mv
        esc_bus_current_ma: int | None = module_info.esc_bus_current_ma
        esc_motor_current_ma: int | None = module_info.esc_motor_current_ma
        esc_index: int | None = module_info.esc_index
        esc_temp_mos_celcius: int | None = module_info.esc_temp_mos_celcius
        esc_temp_capacitor_celcius: int | None = module_info.esc_temp_capacitor_celcius
        esc_temp_mcu_celcius: int | None = module_info.esc_temp_mcu_celcius
        esc_temp_motor_celcius: int | None = module_info.esc_temp_motor_celcius
        esc_running_error: int | None = module_info.esc_running_error
        esc_uptime: int | None = module_info.esc_uptime
        applied_psu: int | None = module_info.applied_psu
        psu_v_in: float | None = module_info.psu_v_in
        psu_i_in: float | None = module_info.psu_i_in
        psu_p_in: float | None = module_info.psu_p_in
        psu_v_out: float | None = module_info.psu_v_out
        psu_i_out: float | None = module_info.psu_i_out
        psu_p_out: float | None = module_info.psu_p_out
        psu_temp1: float | None = module_info.psu_temp1
        psu_temp2: float | None = module_info.psu_temp2
        psu_temp3: float | None = module_info.psu_temp3

        print("ESC Data:")
        print(f"\tRPM: {esc_rpm}")
        print(f"\tApplied PWM (us): {applied_pwm_us}")
        print(f"\tVoltage (mV): {esc_voltage_mv}")
        print(f"\tBus Current (mA): {esc_bus_current_ma}")
        print(f"\tMotor Current (mA): {esc_motor_current_ma}")
        print(f"\tESC Index: {esc_index}")
        print(f"\tTemp MOS (°C): {esc_temp_mos_celcius}")
        print(f"\tTemp Capacitor (°C): {esc_temp_capacitor_celcius}")
        print(f"\tTemp MCU (°C): {esc_temp_mcu_celcius}")
        print(f"\tTemp Motor (°C): {esc_temp_motor_celcius}")
        print(f"\tRunning Error: {esc_running_error}")
        print(f"\tUptime (s): {esc_uptime}")

        print("PSU Data:")
        print(f"\tApplied PSU: {applied_psu}")

        print(f"\tIN : {psu_v_in} V | {psu_i_in} A | {psu_p_in} W")
        print(f"\tOUT: {psu_v_out} V | {psu_i_out} A | {psu_p_out} W")

        print(f"\tTemps: {psu_temp1} °C | {psu_temp2} °C | {psu_temp3} °C")

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

                print(f"\t\tFan {fan_index}:")
                print(f"\t\t\tTarget PWM: {target_pwm:.2f}")
                print(f"\t\t\tCurrent PWM: {current_pwm:.2f}")
                print(f"\t\t\tCurrent RPM: {current_rpm:.2f}")

    print("-" * 20)


stop_event = threading.Event()


def main() -> None:
    """Main function to run the WindSuite SDK example."""
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    sdk.register_module_update_callback(callback=on_module_update)

    sdk.start_communication()

    freq_hz = 25
    try:
        sdk.set_psu(state=True)
        stop_event.wait(timeout=2)

        sdk.fan_controller.set_intensity(percent=30)
        sdk.fan_controller.apply()

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

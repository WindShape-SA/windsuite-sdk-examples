import os

from dotenv import load_dotenv
from windsuite_sdk import WindsuiteSDK

load_dotenv()

SERVER_IP_ADDRESS = os.getenv("SERVER_IP_ADDRESS", default="192.168.88.40")


def main() -> None:
    base_url = f"http://{SERVER_IP_ADDRESS}"

    print(f"Connecting to WindSuite server at {base_url}")

    sdk = WindsuiteSDK(base_url=base_url)

    # ! Get the available layouts and the currently active one.
    layouts = sdk.layouts.get_available_layouts()

    print(f"\nAvailable layouts: {layouts.names}")
    print(f"Current layout: {layouts.current}")

    # ! Switch to the first available layout.
    sdk.layouts.set_layout(layouts.names[0])

    # ! Show the current layout after switching.
    layouts = sdk.layouts.get_available_layouts()
    print(f"Current layout: {layouts.current}")


if __name__ == "__main__":
    main()

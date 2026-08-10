# WINDSUITE SDK EXAMPLES

This contains examples demonstrating how to use the WindSuite SDK.


## Getting Started

In order to run theses examples, you'll need [Astral uv](https://docs.astral.sh/uv/getting-started/installation/) installed on your machine.

1. Clone the examples repository:

```bash
git clone git@github.com:WindShape-SA/windsuite-sdk-examples.git
cd windsuite-sdk-examples
```

2. Install dependencies:

```bash
# This creates a venv and installs the required packages
uv sync
```

3. Run an example:

```bash
cd examples
uv run dynamic_checkers_pattern.py
```

By default, examples connect to `192.168.88.40`, the WindSuite server's default IP address.

If your server uses a different address, override it with an environment variable instead of editing the scripts:

```bash
export SERVER_IP_ADDRESS="172.16.20.190"
uv run dynamic_checkers_pattern.py
```

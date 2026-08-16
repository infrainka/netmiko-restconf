import argparse
import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

parser = argparse.ArgumentParser(
    description="Pull interface state, CDP neighbors, and running-config from a device."
)
parser.add_argument(
    "--device", required=True, choices=["switch", "router"],
    help="Which device to pull from — determines which env-var prefix to use.",
)
args = parser.parse_args()
prefix = args.device.upper()  # "SWITCH" or "ROUTER"

device_params = {
    "device_type": "cisco_ios",
    "host": os.getenv(f"{prefix}_IP"),
    "username": os.getenv(f"{prefix}_USER"),
    "password": os.getenv(f"{prefix}_PASS"),
}

missing = [k for k, v in device_params.items() if k != "device_type" and not v]
if missing:
    raise SystemExit(
        f"Missing required environment variables for {args.device}: "
        f"{prefix}_IP / {prefix}_USER / {prefix}_PASS"
    )

print(f"Connecting to {args.device} at {device_params['host']}...")
try:
    conn = ConnectHandler(**device_params)
    print("Connection successful!\n")

    print("--- show ip interface brief ---")
    print(conn.send_command("show ip interface brief"))

    print("\n--- show cdp neighbors detail ---")
    print(conn.send_command("show cdp neighbors detail"))

    print("\n--- show running-config ---")
    print(conn.send_command("show running-config"))

    conn.disconnect()
except Exception as e:
    print(f"Failed to connect or execute command: {e}")
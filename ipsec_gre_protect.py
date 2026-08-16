import argparse
import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

parser = argparse.ArgumentParser(
    description="Push IPsec protection (tunnel protection) onto an existing GRE tunnel."
)
parser.add_argument(
    "--device", required=True, choices=["switch", "router"],
    help="Which device to configure — determines which env-var prefix and peer to use.",
)
args = parser.parse_args()
prefix = args.device.upper()  # "SWITCH" or "ROUTER"

device_params = {
    "device_type": "cisco_ios",
    "host": os.getenv(f"{prefix}_IP"),
    "username": os.getenv(f"{prefix}_USER"),
    "password": os.getenv(f"{prefix}_PASS"),
    "session_log": f"ipsec_{args.device}_session.txt",
}

# Local tunnel ID + the peer's underlay IP (already defined for the GRE tunnel itself —
# the ISAKMP peer is the same address used as the GRE tunnel destination).
TUNNEL_ID = os.getenv(f"{prefix}_TUNNEL_ID", "0")
PEER_IP = os.getenv(f"{prefix}_TUNNEL_DEST_IP")

# Shared IPsec parameters (same on both ends)
PSK = os.getenv("IPSEC_PSK")
ISAKMP_POLICY = os.getenv("IPSEC_ISAKMP_POLICY", "10")
ISAKMP_ENCRYPTION = os.getenv("IPSEC_ISAKMP_ENCRYPTION", "aes 256")
ISAKMP_HASH = os.getenv("IPSEC_ISAKMP_HASH", "sha256")
ISAKMP_DH_GROUP = os.getenv("IPSEC_ISAKMP_DH_GROUP", "14")
TRANSFORM_SET_NAME = os.getenv("IPSEC_TRANSFORM_SET_NAME", "GRE-PROTECT")
ESP_ENCRYPTION = os.getenv("IPSEC_ESP_ENCRYPTION", "esp-aes 256")
ESP_HASH = os.getenv("IPSEC_ESP_HASH", "esp-sha256-hmac")
PROFILE_NAME = os.getenv("IPSEC_PROFILE_NAME", "GRE-IPSEC-PROFILE")

REQUIRED = {
    f"{prefix}_TUNNEL_DEST_IP": PEER_IP,
    "IPSEC_PSK": PSK,
}
missing = [k for k, v in REQUIRED.items() if not v]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

commands = [
    f"crypto isakmp policy {ISAKMP_POLICY}",
    f"encryption {ISAKMP_ENCRYPTION}",
    f"hash {ISAKMP_HASH}",
    "authentication pre-share",
    f"group {ISAKMP_DH_GROUP}",
    "exit",
    f"crypto isakmp key {PSK} address {PEER_IP}",
    f"crypto ipsec transform-set {TRANSFORM_SET_NAME} {ESP_ENCRYPTION} {ESP_HASH}",
    "mode transport",
    "exit",
    f"crypto ipsec profile {PROFILE_NAME}",
    f"set transform-set {TRANSFORM_SET_NAME}",
    "exit",
    f"interface Tunnel{TUNNEL_ID}",
    f"tunnel protection ipsec profile {PROFILE_NAME}",
]

print(f"Connecting to {args.device} at {device_params['host']}...")
try:
    conn = ConnectHandler(**device_params)
    print("Connection successful!\n")

    print(f"Pushing GRE-over-IPsec config (peer {PEER_IP})...")
    output = conn.send_config_set(commands)
    print(output)

    conn.save_config()
    print("\nConfig saved.")

    conn.disconnect()
except Exception as e:
    print(f"Failed to connect or execute command: {e}")

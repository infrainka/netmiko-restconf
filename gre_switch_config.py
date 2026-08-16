import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()

catalyst = {
    "device_type": "cisco_ios",
    "host": os.getenv("SWITCH_IP"),
    "username": os.getenv("SWITCH_USER"),
    "password": os.getenv("SWITCH_PASS"),
    "session_log": "gre_switch_session.txt",
}

# Tunnel parameters read from environmental variables
TUNNEL_ID = os.getenv("SWITCH_TUNNEL_ID", "0")
TUNNEL_SOURCE_INTF = os.getenv("SWITCH_TUNNEL_SOURCE_INTF")
TUNNEL_DEST_IP = os.getenv("SWITCH_TUNNEL_DEST_IP")
TUNNEL_IP = os.getenv("SWITCH_TUNNEL_IP")
TUNNEL_MASK = os.getenv("SWITCH_TUNNEL_MASK")
TUNNEL_DESCRIPTION = os.getenv("SWITCH_TUNNEL_DESCRIPTION", "GRE_tunnel")

REQUIRED = {
    "SWITCH_TUNNEL_SOURCE_INTF": TUNNEL_SOURCE_INTF,
    "SWITCH_TUNNEL_DEST_IP": TUNNEL_DEST_IP,
    "SWITCH_TUNNEL_IP": TUNNEL_IP,
    "SWITCH_TUNNEL_MASK": TUNNEL_MASK,
}
missing = [k for k, v in REQUIRED.items() if not v]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

commands = [
    f"interface Tunnel{TUNNEL_ID}",
    f"description {TUNNEL_DESCRIPTION}",
    f"ip address {TUNNEL_IP} {TUNNEL_MASK}",
    f"tunnel source {TUNNEL_SOURCE_INTF}",
    f"tunnel destination {TUNNEL_DEST_IP}",
    "tunnel mode gre ip",
    "no shutdown",
]

print(f"Connecting to switch at {catalyst['host']}...")
try:
    conn = ConnectHandler(**catalyst)
    print("Connection successful!\n")

    print(f"Pushing GRE tunnel config to Tunnel{TUNNEL_ID}...")
    output = conn.send_config_set(commands)
    print(output)

    conn.save_config()
    print("\nConfig saved.")

    print("\n--- Verifying tunnel interface ---")
    print(conn.send_command(f"show interfaces tunnel {TUNNEL_ID}"))
    print(conn.send_command("show ip interface brief | include Tunnel"))

    conn.disconnect()
except Exception as e:
    print(f"Failed to connect or execute command: {e}")

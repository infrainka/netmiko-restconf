import os
from dotenv import load_dotenv
from netmiko import ConnectHandler

load_dotenv()


def get_device_params(prefix):
    return {
        "device_type": "cisco_ios",
        "host": os.getenv(f"{prefix}_IP"),
        "username": os.getenv(f"{prefix}_USER"),
        "password": os.getenv(f"{prefix}_PASS"),
    }


def verify_device(label, prefix):
    tunnel_id = os.getenv(f"{prefix}_TUNNEL_ID", "0")
    device_params = get_device_params(prefix)

    print("=" * 70)
    print(f" {label}  ({device_params['host']})")
    print("=" * 70)

    try:
        conn = ConnectHandler(**device_params)
    except Exception as e:
        print(f"  Connection failed: {e}\n")
        return

    print(f"\n--- GRE Tunnel{tunnel_id} state ---")
    print(conn.send_command(f"show interfaces tunnel {tunnel_id} | include line protocol|Tunnel source|Tunnel protocol"))

    print("\n--- ISAKMP (IKE Phase 1) SA state ---")
    print("Expect state QM_IDLE — confirms the encrypted control channel is up.")
    print(conn.send_command("show crypto isakmp sa"))

    print("\n--- IPsec (IKE Phase 2) SA — packet counters ---")
    print("Non-zero '# pkts encrypt' / '# pkts decrypt' confirms traffic is actually being encrypted.")
    print(conn.send_command("show crypto ipsec sa | include interface|current_peer|pkts encrypt|pkts decrypt"))

    conn.disconnect()
    print()


if __name__ == "__main__":
    switch_label = os.getenv("SWITCH_LABEL", "Switch")
    router_label = os.getenv("ROUTER_LABEL", "Router")

    verify_device(switch_label, "SWITCH")
    verify_device(router_label, "ROUTER")

    switch_tunnel_ip = os.getenv("SWITCH_TUNNEL_IP")
    router_tunnel_ip = os.getenv("ROUTER_TUNNEL_IP")

    print("=" * 70)
    print(" Tip: run a few pings across the tunnel BEFORE this script so the")
    print(" packet counters above are non-zero and visibly prove encryption:")
    if router_tunnel_ip:
        print(f"   from switch: ping {router_tunnel_ip}")
    if switch_tunnel_ip:
        print(f"   from router: ping {switch_tunnel_ip}")
    print("=" * 70)

import requests
import urllib3
import json
import os
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router_ip = os.getenv("ROUTER_IP")
username = os.getenv("ROUTER_USER")
password = os.getenv("ROUTER_PASS")

headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}

# Tunnel parameters read from environment, not hardcoded
TUNNEL_ID = os.getenv("ROUTER_TUNNEL_ID", "0")
TUNNEL_SOURCE_INTF = os.getenv("ROUTER_TUNNEL_SOURCE_INTF")
TUNNEL_DEST_IP = os.getenv("ROUTER_TUNNEL_DEST_IP")
TUNNEL_IP = os.getenv("ROUTER_TUNNEL_IP")
TUNNEL_MASK = os.getenv("ROUTER_TUNNEL_MASK")
TUNNEL_DESCRIPTION = os.getenv("ROUTER_TUNNEL_DESCRIPTION", "GRE_tunnel")

REQUIRED = {
    "ROUTER_TUNNEL_SOURCE_INTF": TUNNEL_SOURCE_INTF,
    "ROUTER_TUNNEL_DEST_IP": TUNNEL_DEST_IP,
    "ROUTER_TUNNEL_IP": TUNNEL_IP,
    "ROUTER_TUNNEL_MASK": TUNNEL_MASK,
}
missing = [k for k, v in REQUIRED.items() if not v]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

# Note: an ietf-yang-library / ietf-restconf-monitoring capability check was tried here
# to pre-flight whether Cisco-IOS-XE-tunnel is supported, but on this IOS-XE version
# (16.6.4) it reported the module as absent even when the PUT below succeeded using it.
# Rather than keep a check that can actively contradict the real result, we rely on the
# PUT response itself as the source of truth — see the error handling below.

# --- Push the Tunnel interface via the native model ---
tunnel_url = f"https://{router_ip}/restconf/data/Cisco-IOS-XE-native:native/interface/Tunnel={TUNNEL_ID}"

payload = {
    "Cisco-IOS-XE-native:Tunnel": {
        "name": int(TUNNEL_ID),
        "description": TUNNEL_DESCRIPTION,
        "ip": {
            "address": {
                "primary": {
                    "address": TUNNEL_IP,
                    "mask": TUNNEL_MASK,
                }
            }
        },
        # "tunnel" is defined in a separate augmentation module (Cisco-IOS-XE-tunnel),
        # not the base Cisco-IOS-XE-native module, so it needs its own module prefix here.
        # Note: on this IOS-XE version (16.6.4), "destination" is a plain string leaf,
        # NOT a container with an "address" child — confirmed via a 400 error that
        # named the exact wrong node. This may differ on newer IOS-XE releases; if you
        # get a "malformed-message" / "unknown element" error, read error-path in the
        # response body, it tells you precisely which node is wrong.
        "Cisco-IOS-XE-tunnel:tunnel": {
            "source": TUNNEL_SOURCE_INTF,
            "destination": TUNNEL_DEST_IP,
            "mode": {"gre": {"ip": {}}},
        },
    }
}

print(f"\nPushing Tunnel{TUNNEL_ID} config to {tunnel_url}...")
try:
    resp = requests.put(
        tunnel_url,
        auth=(username, password),
        headers=headers,
        data=json.dumps(payload),
        verify=False,
    )
    print(f"Status: {resp.status_code}")
    if resp.text:
        print(resp.text)
    resp.raise_for_status()
    print(f"\nTunnel{TUNNEL_ID} pushed successfully.")
except requests.exceptions.HTTPError as errh:
    print(f"HTTP Error: {errh}")
    print("If this 404s/400s, the native Tunnel container may differ on this IOS-XE version —")
    print("fall back to Netmiko for this device, same pattern as gre_switch_config.py.")
except Exception as e:
    print(f"An error occurred: {e}")

# --- Verify via GET ---
print("\n--- Verifying via ietf-interfaces GET ---")
verify_url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces/interface=Tunnel{TUNNEL_ID}"
try:
    resp = requests.get(verify_url, auth=(username, password), headers=headers, verify=False)
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=4))
except Exception as e:
    print(f"Verification GET failed: {e}")
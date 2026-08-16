# Network Automation: Cisco IOS/IOS-XE Automation via Netmiko & RESTCONF

> **Quick heads-up before you start:** Make sure you have the required Python packages installed! You can grab them all at once by running:
> `pip install -r requirements.txt`

This repository contains Python scripts demonstrating network automation and data extraction/configuration on Cisco IOS/IOS-XE devices, using two approaches:

1. **CLI automation via Netmiko:** connecting over SSH to execute and parse CLI commands, or push configuration, on devices without full RESTCONF/YANG support.
2. **Model-driven programmability via RESTCONF:** interacting with structured YANG-modeled data over HTTPS on devices that support it.

The scripts started as simple read-only polling/parsing examples and have grown into a small GRE-over-IPsec site-to-site lab, built entirely through Python rather than manual CLI configuration.

---

## Scripts

### Read-only / polling

#### `netmiko_3750.py`
Connects to a Cisco switch via SSH using Netmiko. Executes `show ip ospf neighbor` and uses regex to extract and print only the Neighbor IDs and their current adjacency states.

#### `restconf_4451.py`
Connects to a Cisco router via the RESTCONF API. Queries the `ietf-interfaces:interfaces` endpoint and returns interface configuration/operational state as structured JSON.

#### `pull_interface_data.py`
Pulls a device's interface state, CDP neighbors, and full running-config in one pass. Useful for reconstructing a topology, since interface brief, CDP detail, and running-config together are enough to map out addressing and adjacencies without touching the device further. Prints raw text output rather than parsing it. Same `--device {switch,router}` pattern as `ipsec_gre_protect.py`, reading credentials from `.env`:
```bash
python pull_interface_data.py --device switch
python pull_interface_data.py --device router
```

### Configuration push


#### `gre_switch_config.py`
Pushes GRE tunnel configuration to the switch via Netmiko (CLI). All tunnel parameters (source interface, destination IP, tunnel IP/mask, description) are read from environment variables rather than hardcoded, so the script works against any topology, not just this lab's. Verifies the tunnel came up via `show interfaces tunnel` and `show ip interface brief`.

#### `gre_router_config.py`
Pushes GRE tunnel configuration to the router via RESTCONF, using the `Cisco-IOS-XE-native` model with the `Cisco-IOS-XE-tunnel` augmentation for tunnel source/destination/mode. Same env-var-driven parameterization as the switch script. Verifies via a follow-up `ietf-interfaces` GET.

> **Note on RESTCONF quirks:** the exact shape of the `tunnel` container (e.g. whether `destination` is a plain string leaf or a nested object) is undocumented and appears to vary across IOS-XE releases. If you hit a `400 malformed-message` error, read the `error-path` in the response body. It names the exact node that's wrong, which is how this script's payload structure was worked out for IOS-XE 16.6.4.

#### `ipsec_gre_protect.py`
Adds IPsec protection (`tunnel protection ipsec profile`) to an existing GRE tunnel, via Netmiko CLI on both ends. One script, run twice with a `--device` flag:
```bash
python ipsec_gre_protect.py --device switch
python ipsec_gre_protect.py --device router
```
Configures ISAKMP policy (Phase 1), a transform-set + IPsec profile (Phase 2), and applies the profile to the tunnel interface. Shared parameters (pre-shared key, encryption/hash/DH group) are read from a single set of env vars used by both invocations, so the two ends can't drift out of sync with each other. A mismatch here (e.g. differing PSKs) causes IKE negotiation to fail silently, so keeping both sides reading from one source of truth matters more than it does for the GRE-only scripts.

### Verification

#### `verify_gre_ipsec.py`
Connects to both devices and pulls live state in one pass: GRE tunnel line-protocol status, ISAKMP SA state (`QM_IDLE` confirms the encrypted control channel negotiated), and IPsec SA packet counters (non-zero encrypt/decrypt counts confirm traffic is actually being encrypted, not just that config was accepted). Formatted for readability, useful for a before/after screenshot to confirm the tunnel is really passing encrypted traffic, not just configured.

```bash
# ping across the tunnel first so the counters aren't at zero
python verify_gre_ipsec.py
```

---

## Prerequisites

- Python 3.6+
- Network reachability to your target devices
- Devices configured for SSH (Netmiko scripts) and/or RESTCONF (RESTCONF scripts)

## Installation

```bash
git clone https://github.com/infrainka/netmiko-restconf.git
cd netmiko-restconf
pip install -r requirements.txt
```

> `requirements.txt` should include `netmiko`, `requests`, and `python-dotenv`.

## Security & Environment Variables

This project uses `python-dotenv` to manage credentials and topology parameters. **Never hardcode credentials, IPs, or pre-shared keys in the scripts.** Everything topology- or secret-specific is read from `.env`, which keeps the scripts reusable against any lab rather than just this one.

Copy `.env.example` to `.env` and fill in your own values:

```bash
cp .env.example .env
```

```ini
# --- Device credentials ---
SWITCH_IP=192.168.x.x
SWITCH_USER=your_ssh_username
SWITCH_PASS=your_ssh_password

ROUTER_IP=192.168.x.x
ROUTER_USER=your_restconf_username
ROUTER_PASS=your_restconf_password

# --- Optional display labels used in verify_gre_ipsec.py output ---
SWITCH_LABEL=Switch
ROUTER_LABEL=Router

# --- GRE tunnel parameters: switch side ---
SWITCH_TUNNEL_ID=0
SWITCH_TUNNEL_SOURCE_INTF=GigabitEthernet1/0/7
SWITCH_TUNNEL_DEST_IP=10.x.x.x
SWITCH_TUNNEL_IP=192.168.200.1
SWITCH_TUNNEL_MASK=255.255.255.252
SWITCH_TUNNEL_DESCRIPTION=GRE_to_router

# --- GRE tunnel parameters: router side ---
ROUTER_TUNNEL_ID=0
ROUTER_TUNNEL_SOURCE_INTF=GigabitEthernet0/0/0
ROUTER_TUNNEL_DEST_IP=10.x.x.x
ROUTER_TUNNEL_IP=192.168.200.2
ROUTER_TUNNEL_MASK=255.255.255.252
ROUTER_TUNNEL_DESCRIPTION=GRE_to_switch

# --- IPsec (GRE protection) parameters, shared between both ends ---
IPSEC_PSK=your-pre-shared-key
IPSEC_ISAKMP_POLICY=10
IPSEC_ISAKMP_ENCRYPTION=aes 256
IPSEC_ISAKMP_HASH=sha256
IPSEC_ISAKMP_DH_GROUP=14
IPSEC_TRANSFORM_SET_NAME=GRE-PROTECT
IPSEC_ESP_ENCRYPTION=esp-aes 256
IPSEC_ESP_HASH=esp-sha256-hmac
IPSEC_PROFILE_NAME=GRE-IPSEC-PROFILE
```

> ⚠️ **Important Git Note:** `.gitignore` should include:
>
> ```
> .env
> *.txt
> __pycache__/
> ```
>
> This keeps `.env` (credentials/secrets) and all `*_session.txt` / log files out of version control.

## Usage

```bash
# Read-only polling
python netmiko_3750.py
python restconf_4451.py
python pull_interface_data.py --device switch
python pull_interface_data.py --device router

# GRE tunnel setup
python gre_switch_config.py
python gre_router_config.py

# IPsec protection for the GRE tunnel
python ipsec_gre_protect.py --device switch
python ipsec_gre_protect.py --device router

# Verify the full GRE-over-IPsec stack is actually up and encrypting
python verify_gre_ipsec.py
```

## Lessons learned / troubleshooting notes

A few non-obvious things hit during this build, kept here so they're not re-discovered from scratch next time:

- **Older IOS SSH servers may need legacy client flags.** Modern OpenSSH clients disable old KEX/host-key algorithms by default. If you see `no matching key exchange method` or `no matching host key type`, add the relevant `-oKexAlgorithms=+...` / `-oHostKeyAlgorithms=+...` flags (or a `Host` block in `~/.ssh/config`) rather than assuming the device is misconfigured.
- **RESTCONF payload structure for tunnel interfaces is undocumented and version-specific.** Worked out by reading `error-path` in successive `400` responses rather than from any official schema reference. See the note under `gre_router_config.py` above.
- **Shared IPsec parameters read from one set of env vars, not duplicated per device**, specifically to prevent the PSK/encryption/hash/DH group from silently drifting out of sync between the two ends. A mismatch there fails IKE negotiation without an obviously clear error.
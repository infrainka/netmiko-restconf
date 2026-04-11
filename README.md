# Network Automation: Netmiko OSPF Parsing & RESTCONF Interface Polling

> **Quick heads-up before you start:** Make sure you have the required Python packages installed! You can grab them all at once by running:
> `pip install netmiko requests urllib3 python-dotenv`

This repository contains Python scripts demonstrating two distinct approaches to network automation and data extraction on Cisco IOS/IOS-XE devices:

1. **CLI Scraping & Regex Parsing:** Using `netmiko` to connect to legacy devices, execute CLI commands, and parse the unstructured output using Regular Expressions.
2. **Model-Driven Programmability:** Using `requests` to interact with the RESTCONF API, retrieving structured JSON data directly from the device.

---

## Scripts

### 1. `netmiko_3750.py`

Connects to a Cisco switch via SSH using Netmiko. It executes `show ip ospf neighbor`, bypasses the visual noise of the raw output, and uses Regex to extract and print only the Neighbor IDs and their current adjacency states.

**Example Output:**

```text
Connecting to 192.168.x.x...
Connection successful!
Sending command: 'show ip ospf neighbor'
--- Parsed OSPF Data ---
Neighbor 10.x.x.x is currently in state: FULL/DR
Neighbor 1.x.x.x is currently in state: FULL/BDR
```

### 2. `restconf_4451.py`

Connects to a Cisco router via the RESTCONF API. It queries the `ietf-interfaces:interfaces` endpoint and returns the configuration and operational state of the interfaces in structured, machine-readable JSON format.

**Example Output:**

```text
Querying RESTCONF API at https://10.x.x.x/restconf/data/ietf-interfaces:interfaces...
--- RESTCONF JSON Output ---
{
    "ietf-interfaces:interfaces": {
        "interface": [
            {
                "name": "GigabitEthernet0",
                "type": "iana-if-type:ethernetCsmacd",
                "enabled": true,
                "ietf-ip:ipv4": {},
                "ietf-ip:ipv6": {}
            },
            {
                "name": "GigabitEthernet0/0/0",
                "description": "Transit-To-L3-Switch",
                "type": "iana-if-type:ethernetCsmacd",
                "enabled": true,
                "ietf-ip:ipv4": {
                    "address": [
                        {
                            "ip": "10.x.x.x",
                            "netmask": "255.255.255.252"
                        }
                    ]
                },
                ...
            }
            ...
        ]
    }
}
```

---

## Prerequisites

- Python 3.6+
- Network reachability to your target devices
- Target devices must be configured for SSH (Script 1) and RESTCONF (Script 2)

## Installation

Clone the repository and install the required Python packages:

```bash
git clone https://github.com/infrainka/netmiko-restconf.git
cd netmiko-restconf
pip install -r requirements.txt
```

> **Note:** Ensure your `requirements.txt` includes `netmiko`, `requests`, and `python-dotenv`.

## Security & Environment Variables

This project uses `python-dotenv` to manage credentials securely. **Never hardcode your credentials in the scripts.**

Create a file named `.env` in the root directory of this project and populate it with your specific lab or production variables:

```ini
# .env file

# Switch variables for netmiko_3750.py
SWITCH_IP=192.168.x.x
SWITCH_USER=your_ssh_username
SWITCH_PASS=your_ssh_password

# Router variables for restconf_4451.py
ROUTER_IP=192.168.x.x
ROUTER_USER=your_restconf_username
ROUTER_PASS=your_restconf_password
```

> ⚠️ **Important Git Note:** Ensure your `.gitignore` includes the following entries so you don't accidentally leak credentials or session logs to version control:
>
> ```
> .env
> ssh_log.txt
> __pycache__/
> ```

## Usage

Run the scripts directly from your terminal:

```bash
python netmiko_3750.py
python restconf_4451.py
```
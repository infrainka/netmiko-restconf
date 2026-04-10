import os
from dotenv import load_dotenv
from netmiko import ConnectHandler
import re

load_dotenv()

catalyst_3750 = {
    "device_type": "cisco_ios",
    "host": os.getenv("SWITCH_IP"),
    "username": os.getenv("SWITCH_USER"),
    "password": os.getenv("SWITCH_PASS"),
    "session_log": "ssh_log.txt"
}

print(f"Connecting to {catalyst_3750['host']}...")
try:
    net_connect = ConnectHandler(**catalyst_3750)
    print("Connection successful!\n")
    
    command = "show ip ospf neighbor"
    print(f"Sending command: '{command}'\n")
    output = net_connect.send_command(command)
    
   # print("--- Output Start ---")
   # print(output)
   # print("--- Output End ---")

    pattern = r"(\d{1,3}(?:\.\d{1,3}){3})\s+\d+\s+([A-Z/]+)"

    # re.findall searches the entire raw string and returns a list of matched groups
    matches = re.findall(pattern, output)

    print("--- Parsed OSPF Data ---")
    if matches:
        for neighbor_ip, state in matches:
            print(f"Neighbor {neighbor_ip} is currently in state: {state}")
    else:
        print("No OSPF neighbors found or Regex pattern did not match.")
    
    net_connect.disconnect()

except Exception as e:
    print(f"Failed to connect or execute command: {e}")

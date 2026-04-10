import requests
import urllib3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Disable the warning that pops up when using self-signed certs in a lab
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router_ip = os.getenv("ROUTER_IP")
username = os.getenv("ROUTER_USER")
password = os.getenv("ROUTER_PASS")

# RESTCONF endpoint URL
url = f"https://{router_ip}/restconf/data/ietf-interfaces:interfaces"

headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json"
}

# Make the HTTP GET Request
print(f"Querying RESTCONF API at {url}...")
try:
    response = requests.get(
        url,
        auth=(username, password),
        headers=headers,
        verify=False
    )
    
    # (HTTP 200 OK) ?
    response.raise_for_status()

    json_data = response.json()
    print("\n--- RESTCONF JSON Output ---")
    print(json.dumps(json_data, indent=4))

except requests.exceptions.HTTPError as errh:
    print(f"HTTP Error: {errh}")
except Exception as e:
    print(f"An error occurred: {e}")

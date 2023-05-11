import requests
import sqlite3
import time
from datetime import datetime

# Replace with your API key
MERAKI_API_KEY = "your key"
# Replace with your organization ID
ORGANIZATION_ID = "your org"

# Meraki API URL
URL = f"https://api.meraki.com/api/v1/organizations/{ORGANIZATION_ID}/appliance/uplinks/usage/byNetwork?timespan=60"

# Database setup
conn = sqlite3.connect("/home/admin-az/automation/production/meraki_graphs/meraki_data.db")
cursor = conn.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS meraki_usage
    (time TIMESTAMP, serial TEXT, sent REAL, received REAL, interface TEXT)"""
)
conn.commit()

# API request headers
headers = {
    "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
    "Content-Type": "application/json",
}

def handle_exception(e):
    print(f"Error occurred: {e}")
    print("Waiting 30 seconds before retrying...")
    time.sleep(30)

while True:
    try:
        response = requests.get(URL, headers=headers)
        data = response.json()

        for network in data:
            for uplink in network["byUplink"]:
                sent = ((uplink["sent"] / 60) * 8) / 1000000
                received = ((uplink["received"] / 60) * 8) / 1000000
                interface = uplink["interface"]
                print(f"Inserting data: {datetime.now()}, {uplink['serial']}, {sent}, {received}, {interface}")  # Debug output
                cursor.execute(
                    "INSERT INTO meraki_usage (time, serial, sent, received, interface) VALUES (?, ?, ?, ?, ?)",
                    (datetime.now(), uplink["serial"], sent, received, interface),
                )
                conn.commit()

        time.sleep(60)
    except Exception as e:
        handle_exception(e)

conn.close()

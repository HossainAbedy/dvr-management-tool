# utils.py
import ipaddress
from datetime import datetime
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import subprocess
import xml.etree.ElementTree as ET
import os
import sys


# -----------------------------
# Path Helpers
# -----------------------------
def backend_root():
    """
    Returns absolute path of the BACKEND folder
    regardless of where Python is launched from.
    """
    return os.path.dirname(os.path.abspath(__file__))


def script_path(script_name: str) -> str:
    """
    Returns absolute normalized path to scripts/
    """
    return os.path.join(backend_root(), "scripts", script_name)


# -----------------------------
# IP Generators / Helpers
# -----------------------------
def generate_ips(start_subnet: str, end_subnet: str, last_octet: int):
    start = ipaddress.ip_address(f"{start_subnet}.{last_octet}")
    end = ipaddress.ip_address(f"{end_subnet}.{last_octet}")
    current = start
    while current <= end:
        yield str(current)
        current = ipaddress.ip_address(int(current) + 256)


# -----------------------------
# HTTP Sessions
# -----------------------------
def build_session(vendor: str, username: str, password: str) -> requests.Session:
    session = requests.Session()
    if vendor.lower() == 'hikvision':
        session.auth = HTTPDigestAuth(username, password)
    else:
        session.auth = HTTPBasicAuth(username, password)
    return session


# -----------------------------
# XML Time Parsing
# -----------------------------
def parse_time(xml_text: str) -> str:
    tree = ET.fromstring(xml_text)
    ns = {'ns': tree.tag.split('}')[0].strip('{')} if tree.tag.startswith('{') else {}
    lt = tree.find('.//ns:localTime', ns) if ns else tree.find('.//localTime')
    if lt is None or not lt.text:
        raise ValueError('Missing <localTime>')
    return lt.text


# -----------------------------
# NTP Payload Builder
# -----------------------------
def ntp_payload(vendor: str, ntp: str) -> tuple[str, str]:
    if vendor.lower() == 'hikvision':
        path = '/ISAPI/System/time/NTPServers'
        xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<NTPServerList>
  <NTPServer>
    <id>1</id>
    <addressingFormatType>ipaddress</addressingFormatType>
    <ipAddress>{ntp}</ipAddress>
    <portNo>123</portNo>
    <synchronizeInterval>60</synchronizeInterval>
  </NTPServer>
</NTPServerList>"""
    else:
        path = '/ISAPI/System/time'
        xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<Time>
  <timeMode>1</timeMode>
  <NTP>
    <NTPEnable>true</NTPEnable>
    <PrimaryNTP>{ntp}</PrimaryNTP>
    <SecondaryNTP></SecondaryNTP>
    <SyncInterval>3600</SyncInterval>
  </NTP>
</Time>"""
    return path, xml


# -----------------------------
# PowerShell Runner (Fixed)
# -----------------------------
def run_powershell(ip: str, user: str, old: str, new: str) -> str:
    """
    Safe, guaranteed-working PowerShell runner.
    Uses absolute path, correct quoting, and Win32-safe execution.
    """

    # Absolute path to script
    ps_script = script_path("change_password.ps1")

    if not os.path.isfile(ps_script):
        return f"ERROR: Script not found at {ps_script}"

    powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    if not os.path.isfile(powershell):
        return "ERROR: powershell.exe not found!"

    cmd = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", ps_script,
        "-ip", ip,
        "-user", user,
        "-oldpass", old,
        "-newpass", new
    ]

    try:
        output = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            text=True,
            shell=False  # extremely important; prevents WinError 193
        )
        return output.strip()

    except subprocess.CalledProcessError as e:
        return f"PowerShell ERROR: {e.output.strip()}"

    except Exception as e:
        return f"PowerShell EXCEPTION: {str(e)}"

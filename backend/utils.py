import ipaddress
from datetime import datetime
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import subprocess
import xml.etree.ElementTree as ET


def generate_ips(start_subnet: str, end_subnet: str, last_octet: int):
    start = ipaddress.ip_address(f"{start_subnet}.{last_octet}")
    end = ipaddress.ip_address(f"{end_subnet}.{last_octet}")
    current = start
    while current <= end:
        yield str(current)
        current = ipaddress.ip_address(int(current) + 256)


def build_session(vendor: str, username: str, password: str) -> requests.Session:
    session = requests.Session()
    if vendor.lower() == 'hikvision':
        session.auth = HTTPDigestAuth(username, password)
    else:
        session.auth = HTTPBasicAuth(username, password)
    return session


def parse_time(xml_text: str) -> str:
    tree = ET.fromstring(xml_text)
    ns = {'ns': tree.tag.split('}')[0].strip('{')} if tree.tag.startswith('{') else {}
    lt = tree.find('.//ns:localTime', ns) if ns else tree.find('.//localTime')
    if lt is None or not lt.text:
        raise ValueError('Missing <localTime>')
    return lt.text


def ntp_payload(vendor: str, ntp: str) -> tuple[str,str]:
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


def run_powershell(ip: str, user: str, old: str, new: str) -> str:
    cmd = [
        'powershell.exe', '-ExecutionPolicy', 'Bypass',
        '-File', 'scripts/change_password.ps1',
        '-ip', ip, '-user', user,
        '-oldpass', old, '-newpass', new
    ]
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True).strip()
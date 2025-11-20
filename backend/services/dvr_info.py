#services/dvr_info.py
import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPDigestAuth, HTTPBasicAuth


class DVRInfoService:
    """
    Service to fetch DVR storage and recording time range information.
    """
    def __init__(self, vendor: str, username: str, password: str):
        self.vendor = vendor.lower()
        self.username = username
        self.password = password
        # choose auth method
        if self.vendor == 'hikvision':
            self.auth = HTTPDigestAuth(username, password)
        else:
            self.auth = HTTPBasicAuth(username, password)

    def get_storage_info(self, ip: str) -> dict:
        """
        Returns total and available storage (sum of all HDDs) in device, using ISAPI if supported.
        """
        # Check if storage API is supported via capabilities
        cap_url = f"http://{ip}/ISAPI/System/capabilities"
        try:
            cap_res = requests.get(cap_url, auth=self.auth, timeout=5)
            cap_res.raise_for_status()
            cap_tree = ET.fromstring(cap_res.text)
            ns_uri = cap_tree.tag.split('}')[0].strip('{')
            ns = {'ns': ns_uri}
            support_stats = cap_tree.findtext('.//ns:isSupportResourceStatistics', namespaces=ns)
            if support_stats and support_stats.lower() == 'false':
                raise Exception('Storage API not supported by this device')
        except Exception as e:
            raise Exception(f"Cannot retrieve storage capability: {e}")

        # Use the verified Hikvision storage endpoint
        url = f"http://{ip}/ISAPI/ContentMgmt/storage"
        try:
            r = requests.get(url, auth=self.auth, timeout=5)
            r.raise_for_status()
            tree = ET.fromstring(r.text)
            ns_uri = tree.tag.split('}')[0].strip('{')
            ns = {'ns': ns_uri}
            total, free = 0, 0
            for hdd in tree.findall('.//ns:hdd', ns):
                cap = hdd.findtext('ns:capacity', namespaces=ns)
                fs = hdd.findtext('ns:freeSpace', namespaces=ns)
                total += int(cap or 0)
                free += int(fs or 0)
            return {'total_capacity': total, 'free_space': free}
        except Exception as e:
            raise Exception(f"Error retrieving storage info from {url}: {e}")

    def get_recording_range(self, ip: str) -> dict:
        """
        Returns earliest and latest recording timestamps.
        """
        url = f"http://{ip}/ISAPI/ContentMgmt/record/tracks"
        try:
            r = requests.get(url, auth=self.auth, timeout=5)
            r.raise_for_status()
            tree = ET.fromstring(r.text)
            ns_uri = tree.tag.split('}')[0].strip('{')
            ns = {'ns': ns_uri}
            first = tree.findtext('.//ns:startTime', namespaces=ns)
            last = tree.findtext('.//ns:stopTime', namespaces=ns)
            return {'first_recording': first, 'last_recording': last}
        except Exception as e:
            raise Exception(f"Error retrieving recording range from {url}: {e}")
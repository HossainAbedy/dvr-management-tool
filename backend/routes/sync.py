#routes/sync.py
from flask import Blueprint, request, jsonify
from datetime import datetime
from utils import generate_ips, build_session, parse_time, ntp_payload
from config import Config

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/sync', methods=['POST'])
def sync_range():
    data = request.json
    start, end = data['start'], data['end']
    last = int(data['lastOctet'])
    vendor = data['vendor']
    user, pwd = data['username'], data['password']
    ntp = data.get('ntp', Config.DEFAULT_NTP)

    results = []
    for ip in generate_ips(start, end, last):
        entry = {
            'ip': ip,
            'dvr_time': None,
            'pc_time': datetime.now().isoformat(),
            'status': None,
            'config_url': None
        }
        session = build_session(vendor, user, pwd)
        try:
            # GET time
            get_url = f"http://{ip}/ISAPI/System/time"
            r = session.get(get_url, timeout=3)
            r.raise_for_status()
            entry['dvr_time'] = parse_time(r.text)

            # PUT NTP
            path, xml = ntp_payload(vendor, ntp)
            put_url = f"http://{ip}{path}"
            entry['config_url'] = put_url
            pu = session.put(put_url, data=xml,
                             headers={'Content-Type':'application/xml'}, timeout=3)
            pu.raise_for_status()
            entry['status'] = 'Updated'
        except Exception as e:
            print(f"[ERROR] {ip} → {e}")
            entry['status'] = 'Unreachable' if not entry['dvr_time'] else 'Failed'
        finally:
            session.close()
            results.append(entry)
    return jsonify(results)
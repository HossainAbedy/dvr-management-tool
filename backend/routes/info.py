#routes/info.py
from flask import Blueprint, request, jsonify
from services.dvr_info import DVRInfoService
from utils import generate_ips  # Adjusted to absolute import if app root is `backend/`

info_bp = Blueprint('info', __name__)

@info_bp.route('/info', methods=['POST'])
def batch_dvr_info():
    """
    Expects JSON: {
        "start": "192.168.1.1",
        "end": "192.168.1.254",
        "lastOctet": 254,
        "vendor": "hikvision" or "dahua",
        "username": "admin",
        "password": "12345"
    }
    Returns a list of DVR storage & recording info per IP.
    """
    data = request.get_json()

    # Debug: print received JSON
    print("Incoming data:", data)

    # Validate required fields
    required_fields = ['start', 'end', 'lastOctet', 'vendor', 'username', 'password']
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    start = data.get('start')
    end = data.get('end')
    last = int(data.get('lastOctet'))
    vendor = data.get('vendor')
    user = data.get('username')
    pwd = data.get('password')

    service = DVRInfoService(vendor, user, pwd)

    results = []
    for ip in generate_ips(start, end, last):
        try:
            storage = service.get_storage_info(ip)
            rec_range = service.get_recording_range(ip)
            results.append({
                'ip': ip,
                **storage,
                **rec_range
            })
        except Exception as e:
            results.append({'ip': ip, 'error': str(e)})

    return jsonify(results)

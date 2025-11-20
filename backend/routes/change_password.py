# routes/change_password.py
from flask import Blueprint, request, jsonify
from utils import generate_ips, run_powershell
from concurrent.futures import ThreadPoolExecutor, as_completed

passwd_bp = Blueprint('change_password', __name__)


def _normalize_output_to_status(output: str) -> str:
    """
    Convert raw PowerShell/script output into 'Updated' or 'Failed'.
    Rules:
      - If output contains 'success' (case-insensitive) and NOT 'failed' -> Updated
      - If output contains 'exitcode:0' -> Updated
      - Otherwise -> Failed
    """
    if not isinstance(output, str):
        return "Failed"
    lower = output.lower()
    if "success" in lower and "failed" not in lower:
        return "Updated"
    if "exitcode:0" in lower:
        return "Updated"
    if "updated" in lower:
        return "Updated"
    # treat common HTTP success words as success too
    if "200" in lower and "http" in lower:
        return "Updated"
    return "Failed"


@passwd_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.json or {}

    start = data.get('start')
    end = data.get('end')
    last = int(data.get('lastOctet', 0))
    user = data.get('username')

    old_pw = data.get('oldPassword') or data.get('old_password')
    new_pw = data.get('newPassword') or data.get('new_password')

    if not (start and end and user and old_pw and new_pw):
        return jsonify({
            "error": "Missing required fields",
            "received": data
        }), 400

    ips = list(generate_ips(start, end, last))
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ip = {
            executor.submit(run_powershell, ip, user, old_pw, new_pw): ip
            for ip in ips
        }
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                output = future.result()
                print(f"[PowerShell] {ip} → {output}")
                status = output
            except Exception as e:
                print(f"[PowerShell ERROR] {ip} → {e}")
                status = f"Failed: {e}"
            results.append({'ip': ip, 'status': status})

    return jsonify(results)
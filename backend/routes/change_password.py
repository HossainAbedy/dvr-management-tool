from flask import Blueprint, request, jsonify
from utils import generate_ips, run_powershell

passwd_bp = Blueprint('change_password', __name__)

@passwd_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.json
    start, end = data['start'], data['end']
    last = int(data['lastOctet'])
    user = data['username']
    old_pw, new_pw = data['oldPassword'], data['newPassword']

    results = []
    for ip in generate_ips(start, end, last):
        try:
            output = run_powershell(ip, user, old_pw, new_pw)
            print(f"[PowerShell] {ip} → {output}")
            status = output
        except Exception as e:
            print(f"[PowerShell ERROR] {ip} → {e}")
            status = f"Failed: {e}"
        results.append({'ip': ip, 'status': status})
    return jsonify(results)
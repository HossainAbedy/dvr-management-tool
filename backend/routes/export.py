from flask import Blueprint, request, make_response
import csv
import io

export_bp = Blueprint('export', __name__)

@export_bp.route('/export', methods=['POST'])
def export_csv():
    rows = request.json
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['IP','DVR Time','PC Time','Status','Config URL'])
    for r in rows:
        cw.writerow([r['ip'], r['dvr_time'], r['pc_time'], r['status'], r['config_url']])

    output = make_response(si.getvalue())
    output.headers.update({
        'Content-Disposition':'attachment; filename=dvr_sync.csv',
        'Content-Type':'text/csv'
    })
    return output
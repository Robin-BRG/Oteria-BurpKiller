# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, ReconScan, ReconResult
from datetime import datetime
import threading
import sys
import os

recon_bp = Blueprint('recon', __name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'recon')
sys.path.insert(0, SCRIPTS_DIR)

from http_scanner import scan_http, COMMON_PATHS, AGGRESSIVE_PATHS

@recon_bp.route('/api/investigations/<int:inv_id>/scans', methods=['POST'])
@login_required
def start_scan(inv_id):
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    scan_mode = data.get('scan_mode', 'normal')

    # Calculer le nombre total de paths
    total_paths = len(COMMON_PATHS)
    if scan_mode == 'aggressive':
        total_paths += len(AGGRESSIVE_PATHS)

    scan = ReconScan(
        investigation_id=inv_id,
        started_by_id=current_user.id,
        scan_mode=scan_mode,
        wordlist=data.get('wordlist', 'common'),
        status='running',
        progress_current=0,
        progress_total=total_paths
    )
    db.session.add(scan)
    db.session.commit()

    thread = threading.Thread(
        target=run_scan_task,
        args=(scan.id, investigation.target_url, scan_mode)
    )
    thread.daemon = True
    thread.start()

    return jsonify(scan.to_dict()), 201


def run_scan_task(scan_id, target_url, scan_mode):
    from app import app
    with app.app_context():
        scan = ReconScan.query.get(scan_id)
        if not scan:
            return

        def update_progress(current, total):
            """Callback pour mettre a jour le progres"""
            scan.progress_current = current
            scan.progress_total = total
            db.session.commit()

        try:
            results = scan_http(target_url, scan_mode, progress_callback=update_progress)

            for result in results:
                path = result['path']
                parent = get_parent_path(path)

                recon_result = ReconResult(
                    scan_id=scan_id,
                    path=path,
                    status_code=result.get('status_code'),
                    content_length=result.get('content_length'),
                    content_type=result.get('content_type'),
                    parent_path=parent
                )
                db.session.add(recon_result)

            scan.status = 'completed'
            scan.completed_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            db.session.commit()


def get_parent_path(path):
    if path == '/':
        return None
    parts = path.rstrip('/').rsplit('/', 1)
    if len(parts) == 1:
        return '/'
    return parts[0] if parts[0] else '/'


@recon_bp.route('/api/investigations/<int:inv_id>/scans', methods=['GET'])
@login_required
def list_scans(inv_id):
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    scans = investigation.scans.order_by(ReconScan.created_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])


@recon_bp.route('/api/scans/<int:scan_id>/results', methods=['GET'])
@login_required
def get_scan_results(scan_id):
    scan = ReconScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    results = scan.results.all()
    return jsonify({
        'scan': scan.to_dict(),
        'results': [r.to_dict() for r in results]
    })


@recon_bp.route('/api/scans/<int:scan_id>', methods=['GET'])
@login_required
def get_scan_status(scan_id):
    scan = ReconScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    return jsonify(scan.to_dict())

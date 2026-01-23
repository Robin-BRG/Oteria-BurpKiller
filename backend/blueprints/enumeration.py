# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, EnumScan, EnumResult
from datetime import datetime
import threading
import sys
import os

enum_bp = Blueprint('enumeration', __name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts', 'enum')
sys.path.insert(0, SCRIPTS_DIR)

from tech_detector import analyze_headers


@enum_bp.route('/api/investigations/<int:inv_id>/enum', methods=['POST'])
@login_required
def start_enum_scan(inv_id):
    """Lancer un scan d'enumeration"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    scan = EnumScan(
        investigation_id=inv_id,
        started_by_id=current_user.id,
        status='running'
    )
    db.session.add(scan)
    db.session.commit()

    thread = threading.Thread(
        target=run_enum_task,
        args=(scan.id, investigation.target_url)
    )
    thread.daemon = True
    thread.start()

    return jsonify(scan.to_dict()), 201


def run_enum_task(scan_id, target_url):
    """Executer le scan d'enumeration en arriere-plan"""
    from app import app
    with app.app_context():
        scan = EnumScan.query.get(scan_id)
        if not scan:
            return

        try:
            results = analyze_headers(target_url)

            for result in results:
                enum_result = EnumResult(
                    scan_id=scan_id,
                    result_type=result['type'],
                    category=result['category'],
                    name=result['name'],
                    value=result['value'],
                    confidence=result['confidence'],
                    security_level=result['security_level'],
                    description=result['description']
                )
                db.session.add(enum_result)

            scan.status = 'completed'
            scan.completed_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            db.session.commit()


@enum_bp.route('/api/investigations/<int:inv_id>/enum', methods=['GET'])
@login_required
def list_enum_scans(inv_id):
    """Liste des scans d'enumeration"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    scans = investigation.enum_scans.order_by(EnumScan.created_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])


@enum_bp.route('/api/enum/<int:scan_id>/results', methods=['GET'])
@login_required
def get_enum_results(scan_id):
    """Obtenir les resultats d'un scan d'enumeration"""
    scan = EnumScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    results = scan.results.all()
    return jsonify({
        'scan': scan.to_dict(),
        'results': [r.to_dict() for r in results]
    })


@enum_bp.route('/api/enum/<int:scan_id>', methods=['GET'])
@login_required
def get_enum_status(scan_id):
    """Status d'un scan d'enumeration"""
    scan = EnumScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    return jsonify(scan.to_dict())

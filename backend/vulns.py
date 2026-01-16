# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, VulnerabilityScan, Vulnerability, JsSecret, ReconResult
from datetime import datetime
import threading
import sys
import os

vulns_bp = Blueprint('vulns', __name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

from sqli_scanner import scan_sqli_on_endpoints
from xss_scanner import scan_xss_on_endpoints
from js_secret_scanner import scan_js_secrets


@vulns_bp.route('/api/investigations/<int:inv_id>/vuln-scan', methods=['POST'])
@login_required
def start_vuln_scan(inv_id):
    """Lancer un scan de vulnerabilites"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    scan_type = data.get('scan_type', 'all')  # sqli, xss, all

    # Creer le scan
    scan = VulnerabilityScan(
        investigation_id=inv_id,
        started_by_id=current_user.id,
        scan_type=scan_type,
        status='running'
    )
    db.session.add(scan)
    db.session.commit()

    # Lancer le scan en background
    thread = threading.Thread(
        target=run_vuln_scan,
        args=(scan.id, investigation.target_url)
    )
    thread.daemon = True
    thread.start()

    return jsonify(scan.to_dict()), 201


def run_vuln_scan(scan_id, target_url):
    """Execute le scan de vulnerabilites en arriere-plan"""
    from app import app
    with app.app_context():
        scan = VulnerabilityScan.query.get(scan_id)
        if not scan:
            return

        try:
            investigation = Investigation.query.get(scan.investigation_id)

            # Recuperer les endpoints depuis la recon
            recon_results = ReconResult.query.filter_by(
                scan_id=investigation.scans.first().id if investigation.scans.first() else None
            ).all()

            endpoints = []
            for result in recon_results:
                if result.status_code and 200 <= result.status_code < 300:
                    full_url = target_url.rstrip('/') + result.path
                    endpoints.append({'url': full_url, 'method': 'GET'})

            # Si pas d'endpoints, utiliser juste l'URL de base
            if not endpoints:
                endpoints = [{'url': target_url, 'method': 'GET'}]

            scan.progress_total = len(endpoints)
            db.session.commit()

            all_vulnerabilities = []

            # Scanner SQLi
            if scan.scan_type in ['sqli', 'all']:
                def progress_sqli(current, total):
                    scan.progress_current = current
                    db.session.commit()

                sqli_vulns = scan_sqli_on_endpoints(endpoints, progress_callback=progress_sqli)
                all_vulnerabilities.extend(sqli_vulns)

            # Scanner XSS
            if scan.scan_type in ['xss', 'all']:
                def progress_xss(current, total):
                    scan.progress_current = len(endpoints) + current
                    db.session.commit()

                xss_vulns = scan_xss_on_endpoints(endpoints, progress_callback=progress_xss)
                all_vulnerabilities.extend(xss_vulns)

            # Sauvegarder les vulnerabilites trouvees
            for vuln_data in all_vulnerabilities:
                vuln = Vulnerability(
                    scan_id=scan_id,
                    vuln_type=vuln_data['vuln_type'],
                    severity=vuln_data['severity'],
                    url=vuln_data['url'],
                    parameter=vuln_data.get('parameter'),
                    method=vuln_data.get('method', 'GET'),
                    payload=vuln_data.get('payload'),
                    evidence=vuln_data.get('evidence'),
                    description=vuln_data.get('description'),
                    recommendation=vuln_data.get('recommendation')
                )
                db.session.add(vuln)

            scan.status = 'completed'
            scan.completed_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            db.session.commit()


@vulns_bp.route('/api/investigations/<int:inv_id>/js-scan', methods=['POST'])
@login_required
def start_js_scan(inv_id):
    """Lancer un scan JavaScript pour detecter les secrets"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    # Lancer le scan en background
    thread = threading.Thread(
        target=run_js_scan,
        args=(inv_id, investigation.target_url)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started'}), 201


def run_js_scan(investigation_id, target_url):
    """Execute le scan JavaScript en arriere-plan"""
    from app import app
    with app.app_context():
        try:
            secrets = scan_js_secrets(target_url)

            # Sauvegarder les secrets trouves
            for secret_data in secrets:
                js_secret = JsSecret(
                    investigation_id=investigation_id,
                    secret_type=secret_data['secret_type'],
                    severity=secret_data['severity'],
                    source_url=secret_data['source_url'],
                    secret_value=secret_data['secret_value'],
                    secret_preview=secret_data.get('secret_preview'),
                    context=secret_data.get('context'),
                    description=secret_data.get('description')
                )
                db.session.add(js_secret)

            db.session.commit()

        except Exception as e:
            print(f"Erreur JS scan: {e}")


@vulns_bp.route('/api/investigations/<int:inv_id>/vuln-scans', methods=['GET'])
@login_required
def list_vuln_scans(inv_id):
    """Liste des scans de vulnerabilites"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    scans = investigation.vuln_scans.order_by(VulnerabilityScan.created_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])


@vulns_bp.route('/api/vuln-scans/<int:scan_id>/results', methods=['GET'])
@login_required
def get_vuln_results(scan_id):
    """Obtenir les resultats d'un scan de vulnerabilites"""
    scan = VulnerabilityScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    vulnerabilities = scan.vulnerabilities.all()
    return jsonify({
        'scan': scan.to_dict(),
        'vulnerabilities': [v.to_dict() for v in vulnerabilities]
    })


@vulns_bp.route('/api/investigations/<int:inv_id>/js-secrets', methods=['GET'])
@login_required
def get_js_secrets(inv_id):
    """Obtenir les secrets JavaScript trouves"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    secrets = investigation.js_secrets.order_by(JsSecret.created_at.desc()).all()
    return jsonify([s.to_dict() for s in secrets])


@vulns_bp.route('/api/vuln-scans/<int:scan_id>', methods=['GET'])
@login_required
def get_vuln_scan_status(scan_id):
    """Status d'un scan de vulnerabilites"""
    scan = VulnerabilityScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    return jsonify(scan.to_dict())

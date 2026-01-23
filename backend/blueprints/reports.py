# -*- coding: utf-8 -*-
"""
Module Reports - Génération de rapports PDF et HTML
"""
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Investigation
from report_generator import generate_html_report, generate_pdf_report
from datetime import datetime
import io

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/investigations/<int:inv_id>/report/html', methods=['GET'])
@login_required
def get_html_report(inv_id):
    """Générer un rapport HTML"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorisé'}), 403

    try:
        html_content = generate_html_report(investigation, current_user)

        # Retourner le HTML directement
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

    except Exception as e:
        return jsonify({'error': f'Erreur lors de la génération du rapport: {str(e)}'}), 500


@reports_bp.route('/api/investigations/<int:inv_id>/report/pdf', methods=['GET'])
@login_required
def get_pdf_report(inv_id):
    """Générer et télécharger un rapport PDF"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorisé'}), 403

    try:
        pdf_content = generate_pdf_report(investigation, current_user)

        # Créer un nom de fichier
        filename = f"rapport_{investigation.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Retourner le PDF en tant que fichier téléchargeable
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        error_msg = str(e)

        # Message spécifique pour Windows/GTK
        if 'libgobject' in error_msg or 'GTK' in error_msg:
            return jsonify({
                'error': 'La génération PDF nécessite GTK+ (difficile à installer sur Windows).',
                'workaround': 'Solution: Générer le rapport HTML puis utiliser "Imprimer > Enregistrer en PDF" de votre navigateur.',
                'details': error_msg
            }), 500

        return jsonify({'error': f'Erreur lors de la génération du rapport PDF: {error_msg}'}), 500


@reports_bp.route('/api/investigations/<int:inv_id>/report/preview', methods=['GET'])
@login_required
def preview_report(inv_id):
    """Prévisualiser les données du rapport (JSON)"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorisé'}), 403

    # Retourner un résumé des données qui seront dans le rapport
    summary = {
        'investigation': {
            'id': investigation.id,
            'name': investigation.name,
            'target_url': investigation.target_url,
            'created_at': investigation.created_at.strftime('%Y-%m-%d %H:%M:%S')
        },
        'stats': {
            'recon_scans': investigation.scans.count(),
            'enum_scans': investigation.enum_scans.count(),
            'network_scans': investigation.network_scans.count(),
            'ad_scans': investigation.ad_scans.count(),
            'vuln_scans': investigation.vuln_scans.count(),
            'total_vulnerabilities': sum(scan.vulnerabilities.count() for scan in investigation.vuln_scans),
            'js_secrets': investigation.js_secrets.count(),
            'http_requests': investigation.http_requests.count()
        }
    }

    return jsonify(summary)

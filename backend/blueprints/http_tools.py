# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, HttpRequest
import requests
import time

http_bp = Blueprint('http_tools', __name__)


@http_bp.route('/api/investigations/<int:inv_id>/http-requests', methods=['POST'])
@login_required
def send_http_request(inv_id):
    """Envoyer une requete HTTP manuelle"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()

    # Validation
    if not data.get('method') or not data.get('url'):
        return jsonify({'error': 'Method et URL requis'}), 400

    method = data.get('method', 'GET').upper()
    url = data.get('url')
    headers = data.get('headers', {})
    body = data.get('body', '')

    # Creer l'entree dans la DB
    http_req = HttpRequest(
        investigation_id=inv_id,
        sent_by_id=current_user.id,
        method=method,
        url=url,
        headers=headers,
        body=body if body else None
    )
    db.session.add(http_req)
    db.session.commit()

    # Envoyer la requete
    try:
        start_time = time.time()

        # Preparer les parametres
        req_params = {
            'headers': headers,
            'timeout': 30,
            'allow_redirects': data.get('followRedirects', True),
            'verify': data.get('verifySSL', True)
        }

        # Ajouter le body si applicable
        if method in ['POST', 'PUT', 'PATCH'] and body:
            req_params['data'] = body

        # Envoyer la requete
        response = requests.request(method, url, **req_params)

        response_time = time.time() - start_time

        # Stocker la reponse
        http_req.response_status = response.status_code
        http_req.response_headers = dict(response.headers)
        http_req.response_body = response.text
        http_req.response_time = response_time
        db.session.commit()

        return jsonify(http_req.to_dict()), 200

    except Exception as e:
        http_req.error_message = str(e)
        db.session.commit()
        return jsonify(http_req.to_dict()), 200  # Return 200 meme en cas d'erreur pour avoir les details


@http_bp.route('/api/investigations/<int:inv_id>/http-requests', methods=['GET'])
@login_required
def get_http_requests(inv_id):
    """Liste des requetes HTTP d'une enquete"""
    investigation = Investigation.query.get_or_404(inv_id)
    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    # Recuperer les requetes (plus recentes en premier)
    http_requests = HttpRequest.query.filter_by(investigation_id=inv_id)\
        .order_by(HttpRequest.created_at.desc())\
        .all()

    return jsonify([req.to_dict() for req in http_requests])


@http_bp.route('/api/http-requests/<int:req_id>', methods=['GET'])
@login_required
def get_http_request(req_id):
    """Details d'une requete HTTP specifique"""
    http_req = HttpRequest.query.get_or_404(req_id)
    investigation = Investigation.query.get(http_req.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    return jsonify(http_req.to_dict())


@http_bp.route('/api/http-requests/<int:req_id>', methods=['DELETE'])
@login_required
def delete_http_request(req_id):
    """Supprimer une requete HTTP"""
    http_req = HttpRequest.query.get_or_404(req_id)
    investigation = Investigation.query.get(http_req.investigation_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    db.session.delete(http_req)
    db.session.commit()

    return jsonify({'success': True}), 200

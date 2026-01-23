# -*- coding: utf-8 -*-
"""
Routes API pour les enquetes
"""
import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Investigation, InvestigationMember, InvestigationFile, User

# Dossier pour les fichiers uploades
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'json', 'xml', 'csv', 'html'}

# Creer le dossier uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

investigations_bp = Blueprint('investigations', __name__)


# Liste des enquetes de l'utilisateur
@investigations_bp.route('/api/investigations', methods=['GET'])
@login_required
def list_investigations():
    # Enquetes dont je suis proprietaire
    owned = Investigation.query.filter_by(owner_id=current_user.id).all()

    # Enquetes dont je suis membre
    member_ids = [m.investigation_id for m in current_user.memberships.all()]
    shared = Investigation.query.filter(Investigation.id.in_(member_ids)).all() if member_ids else []

    # Fusionner et serialiser
    all_investigations = owned + shared
    return jsonify([inv.to_dict() for inv in all_investigations])


# Creer une enquete
@investigations_bp.route('/api/investigations', methods=['POST'])
@login_required
def create_investigation():
    data = request.get_json()

    # Validation
    name = data.get('name', '').strip()
    target_url = data.get('target_url', '').strip()

    if not name:
        return jsonify({'error': 'Le nom est requis'}), 400
    if not target_url:
        return jsonify({'error': 'L\'URL cible est requise'}), 400

    # Creer l'enquete
    investigation = Investigation(
        name=name,
        target_url=target_url,
        description=data.get('description', ''),
        is_public=data.get('is_public', False),
        is_collaborative=data.get('is_collaborative', False),
        owner_id=current_user.id
    )

    db.session.add(investigation)
    db.session.commit()

    return jsonify(investigation.to_dict()), 201


# Obtenir une enquete
@investigations_bp.route('/api/investigations/<int:id>', methods=['GET'])
@login_required
def get_investigation(id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    return jsonify(investigation.to_dict())


# Modifier une enquete
@investigations_bp.route('/api/investigations/<int:id>', methods=['PUT'])
@login_required
def update_investigation(id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()

    # Mise a jour des champs
    if 'name' in data:
        investigation.name = data['name'].strip()
    if 'target_url' in data:
        investigation.target_url = data['target_url'].strip()
    if 'description' in data:
        investigation.description = data['description']
    if 'is_public' in data:
        investigation.is_public = data['is_public']
    if 'is_collaborative' in data:
        investigation.is_collaborative = data['is_collaborative']

    db.session.commit()

    return jsonify(investigation.to_dict())


# Supprimer une enquete
@investigations_bp.route('/api/investigations/<int:id>', methods=['DELETE'])
@login_required
def delete_investigation(id):
    investigation = Investigation.query.get_or_404(id)

    # Seul le proprietaire peut supprimer
    if investigation.owner_id != current_user.id:
        return jsonify({'error': 'Seul le proprietaire peut supprimer'}), 403

    db.session.delete(investigation)
    db.session.commit()

    return jsonify({'message': 'Enquete supprimee'})


# Ajouter un membre
@investigations_bp.route('/api/investigations/<int:id>/members', methods=['POST'])
@login_required
def add_member(id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    username = data.get('username', '').strip()
    role = data.get('role', 'viewer')

    if not username:
        return jsonify({'error': 'Username requis'}), 400

    # Trouver l'utilisateur
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Utilisateur non trouve'}), 404

    # Verifier qu'il n'est pas deja membre
    existing = InvestigationMember.query.filter_by(
        investigation_id=id,
        user_id=user.id
    ).first()

    if existing:
        return jsonify({'error': 'Deja membre'}), 400

    # Ajouter le membre
    member = InvestigationMember(
        investigation_id=id,
        user_id=user.id,
        role=role
    )

    db.session.add(member)
    db.session.commit()

    return jsonify(member.to_dict()), 201


# Lister les membres
@investigations_bp.route('/api/investigations/<int:id>/members', methods=['GET'])
@login_required
def list_members(id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    members = investigation.members.all()
    return jsonify([m.to_dict() for m in members])


# Supprimer un membre
@investigations_bp.route('/api/investigations/<int:id>/members/<int:member_id>', methods=['DELETE'])
@login_required
def remove_member(id, member_id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    member = InvestigationMember.query.get_or_404(member_id)

    if member.investigation_id != id:
        return jsonify({'error': 'Membre non trouve'}), 404

    db.session.delete(member)
    db.session.commit()

    return jsonify({'message': 'Membre retire'})


# Lister les fichiers
@investigations_bp.route('/api/investigations/<int:id>/files', methods=['GET'])
@login_required
def list_files(id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    files = investigation.files.all()
    return jsonify([f.to_dict() for f in files])


# Uploader un fichier
@investigations_bp.route('/api/investigations/<int:id>/files', methods=['POST'])
@login_required
def upload_file(id):
    investigation = Investigation.query.get_or_404(id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Aucun fichier selectionne'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Type de fichier non autorise'}), 400

    # Generer un nom unique pour eviter les collisions
    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{extension}"

    # Sauvegarder le fichier
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    # Obtenir la taille du fichier
    file_size = os.path.getsize(file_path)

    # Creer l'entree en base
    file_record = InvestigationFile(
        investigation_id=id,
        uploaded_by_id=current_user.id,
        filename=unique_filename,
        original_filename=original_filename,
        file_type=extension,
        file_size=file_size
    )

    db.session.add(file_record)
    db.session.commit()

    return jsonify(file_record.to_dict()), 201


# Telecharger un fichier
@investigations_bp.route('/api/files/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    file_record = InvestigationFile.query.get_or_404(file_id)
    investigation = Investigation.query.get(file_record.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    return send_from_directory(
        UPLOAD_FOLDER,
        file_record.filename,
        as_attachment=True,
        download_name=file_record.original_filename
    )


# Supprimer un fichier
@investigations_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id):
    file_record = InvestigationFile.query.get_or_404(file_id)
    investigation = Investigation.query.get(file_record.investigation_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    # Supprimer le fichier physique
    file_path = os.path.join(UPLOAD_FOLDER, file_record.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Supprimer l'entree en base
    db.session.delete(file_record)
    db.session.commit()

    return jsonify({'message': 'Fichier supprime'})


# Renommer un fichier
@investigations_bp.route('/api/files/<int:file_id>', methods=['PUT'])
@login_required
def rename_file(file_id):
    file_record = InvestigationFile.query.get_or_404(file_id)
    investigation = Investigation.query.get(file_record.investigation_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    data = request.get_json()
    new_name = data.get('original_filename', '').strip()

    if not new_name:
        return jsonify({'error': 'Nom requis'}), 400

    # Securiser le nouveau nom
    new_name = secure_filename(new_name)
    file_record.original_filename = new_name

    db.session.commit()

    return jsonify(file_record.to_dict())


# Obtenir le contenu d'un fichier texte
@investigations_bp.route('/api/files/<int:file_id>/content', methods=['GET'])
@login_required
def get_file_content(file_id):
    file_record = InvestigationFile.query.get_or_404(file_id)
    investigation = Investigation.query.get(file_record.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Acces refuse'}), 403

    # Types de fichiers texte supportes
    text_types = ['txt', 'json', 'xml', 'csv', 'html', 'css', 'js', 'md', 'log']

    if file_record.file_type.lower() not in text_types:
        return jsonify({'error': 'Type non supporte'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file_record.filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'Fichier non trouve'}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except UnicodeDecodeError:
        # Essayer avec latin-1 si utf-8 echoue
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception:
            return jsonify({'error': 'Impossible de lire le fichier'}), 500

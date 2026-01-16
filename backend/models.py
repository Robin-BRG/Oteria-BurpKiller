# -*- coding: utf-8 -*-
"""
Modeles de base de donnees
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Utilisateur de l'application"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    owned_investigations = db.relationship('Investigation', backref='owner', lazy='dynamic')
    memberships = db.relationship('InvestigationMember', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Investigation(db.Model):
    """Enquete de securite sur une cible"""
    __tablename__ = 'investigations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Visibilite et collaboration
    is_public = db.Column(db.Boolean, default=False)
    is_collaborative = db.Column(db.Boolean, default=False)

    # Proprietaire
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    members = db.relationship('InvestigationMember', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('InvestigationFile', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    scans = db.relationship('ReconScan', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    enum_scans = db.relationship('EnumScan', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    http_requests = db.relationship('HttpRequest', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    vuln_scans = db.relationship('VulnerabilityScan', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    js_secrets = db.relationship('JsSecret', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Investigation {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'target_url': self.target_url,
            'description': self.description,
            'is_public': self.is_public,
            'is_collaborative': self.is_collaborative,
            'owner_id': self.owner_id,
            'owner': self.owner.to_dict() if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def user_can_view(self, user):
        """Verifie si un user peut voir cette enquete"""
        if self.is_public:
            return True
        if user and user.id == self.owner_id:
            return True
        if user and self.members.filter_by(user_id=user.id).first():
            return True
        return False

    def user_can_edit(self, user):
        """Verifie si un user peut modifier cette enquete"""
        if not user:
            return False
        if user.id == self.owner_id:
            return True
        member = self.members.filter_by(user_id=user.id).first()
        if member and member.role in ['editor', 'admin']:
            return True
        return False


class InvestigationMember(db.Model):
    """Membre d'une enquete collaborative"""
    __tablename__ = 'investigation_members'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Role: viewer, editor, admin
    role = db.Column(db.String(20), default='viewer')

    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Contrainte unique: un user ne peut etre membre qu'une fois par enquete
    __table_args__ = (db.UniqueConstraint('investigation_id', 'user_id'),)

    def __repr__(self):
        return f'<InvestigationMember {self.user_id} in {self.investigation_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }


class ReconScan(db.Model):
    """Scan de reconnaissance"""
    __tablename__ = 'recon_scans'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Parametres du scan
    scan_mode = db.Column(db.String(20), default='normal')  # stealth, normal, aggressive
    wordlist = db.Column(db.String(100), default='common')

    # Status: pending, running, completed, failed
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)

    # Progress tracking
    progress_current = db.Column(db.Integer, default=0)
    progress_total = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relations
    started_by = db.relationship('User', backref='started_scans')
    results = db.relationship('ReconResult', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ReconScan {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'scan_mode': self.scan_mode,
            'wordlist': self.wordlist,
            'status': self.status,
            'error_message': self.error_message,
            'progress_current': self.progress_current,
            'progress_total': self.progress_total,
            'started_by': self.started_by.to_dict() if self.started_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results_count': self.results.count()
        }


class ReconResult(db.Model):
    """Resultat de reconnaissance (path decouvert)"""
    __tablename__ = 'recon_results'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('recon_scans.id'), nullable=False)

    # Infos du path
    path = db.Column(db.String(500), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    content_length = db.Column(db.Integer, nullable=True)
    content_type = db.Column(db.String(100), nullable=True)

    # Parent pour construire l'arbre
    parent_path = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ReconResult {self.path}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'path': self.path,
            'status_code': self.status_code,
            'content_length': self.content_length,
            'content_type': self.content_type,
            'parent_path': self.parent_path
        }


class EnumScan(db.Model):
    """Scan d'enumeration (technologies, headers, etc.)"""
    __tablename__ = 'enum_scans'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Status: pending, running, completed, failed
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relations
    started_by = db.relationship('User', backref='started_enum_scans')
    results = db.relationship('EnumResult', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EnumScan {self.id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'status': self.status,
            'error_message': self.error_message,
            'started_by': self.started_by.to_dict() if self.started_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results_count': self.results.count()
        }


class EnumResult(db.Model):
    """Resultat d'enumeration (tech, header, etc.)"""
    __tablename__ = 'enum_results'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('enum_scans.id'), nullable=False)

    # Type: technology, header, subdomain, port, etc.
    result_type = db.Column(db.String(50), nullable=False)

    # Categorie pour les technologies (server, framework, cms, frontend, etc.)
    category = db.Column(db.String(100), nullable=True)

    # Nom (ex: "Nginx", "X-Frame-Options")
    name = db.Column(db.String(200), nullable=False)

    # Valeur/Version (ex: "1.21.0", "DENY")
    value = db.Column(db.Text, nullable=True)

    # Niveau de confiance (low, medium, high)
    confidence = db.Column(db.String(20), default='medium')

    # Niveau de securite pour headers (secure, warning, missing, insecure)
    security_level = db.Column(db.String(20), nullable=True)

    # Description ou recommandation
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EnumResult {self.result_type}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'result_type': self.result_type,
            'category': self.category,
            'name': self.name,
            'value': self.value,
            'confidence': self.confidence,
            'security_level': self.security_level,
            'description': self.description
        }


class HttpRequest(db.Model):
    """Requete HTTP manuelle (Request Builder)"""
    __tablename__ = 'http_requests'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    sent_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Requete
    method = db.Column(db.String(10), nullable=False)  # GET, POST, PUT, DELETE, etc.
    url = db.Column(db.String(1000), nullable=False)
    headers = db.Column(db.JSON, nullable=True)  # Dictionnaire des headers
    body = db.Column(db.Text, nullable=True)

    # Reponse
    response_status = db.Column(db.Integer, nullable=True)
    response_headers = db.Column(db.JSON, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    response_time = db.Column(db.Float, nullable=True)  # En secondes

    # Metadata
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    sent_by = db.relationship('User', backref='http_requests')

    def __repr__(self):
        return f'<HttpRequest {self.method} {self.url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'sent_by': self.sent_by.to_dict() if self.sent_by else None,
            'method': self.method,
            'url': self.url,
            'headers': self.headers,
            'body': self.body,
            'response_status': self.response_status,
            'response_headers': self.response_headers,
            'response_body': self.response_body,
            'response_time': self.response_time,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VulnerabilityScan(db.Model):
    """Scan de vulnerabilites (SQLi, XSS, etc.)"""
    __tablename__ = 'vulnerability_scans'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Type de scan: sqli, xss, all
    scan_type = db.Column(db.String(50), nullable=False)

    # Status: pending, running, completed, failed
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)

    # Progress
    progress_current = db.Column(db.Integer, default=0)
    progress_total = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relations
    started_by = db.relationship('User', backref='started_vuln_scans')
    vulnerabilities = db.relationship('Vulnerability', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<VulnerabilityScan {self.id} - {self.scan_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'scan_type': self.scan_type,
            'status': self.status,
            'error_message': self.error_message,
            'progress_current': self.progress_current,
            'progress_total': self.progress_total,
            'started_by': self.started_by.to_dict() if self.started_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'vulnerabilities_count': self.vulnerabilities.count()
        }


class Vulnerability(db.Model):
    """Vulnerabilite detectee"""
    __tablename__ = 'vulnerabilities'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('vulnerability_scans.id'), nullable=False)

    # Type: sqli, xss, command_injection, etc.
    vuln_type = db.Column(db.String(50), nullable=False)

    # Severite: critical, high, medium, low, info
    severity = db.Column(db.String(20), nullable=False)

    # URL et parametre vulnerable
    url = db.Column(db.String(1000), nullable=False)
    parameter = db.Column(db.String(200), nullable=True)
    method = db.Column(db.String(10), default='GET')

    # Payload qui a fonctionne
    payload = db.Column(db.Text, nullable=True)

    # Preuve (extrait de reponse, error message, etc.)
    evidence = db.Column(db.Text, nullable=True)

    # Description et recommandation
    description = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vulnerability {self.vuln_type} in {self.url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'vuln_type': self.vuln_type,
            'severity': self.severity,
            'url': self.url,
            'parameter': self.parameter,
            'method': self.method,
            'payload': self.payload,
            'evidence': self.evidence,
            'description': self.description,
            'recommendation': self.recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class JsSecret(db.Model):
    """Secret trouve dans le JavaScript"""
    __tablename__ = 'js_secrets'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)

    # Type: api_key, token, password, endpoint, etc.
    secret_type = db.Column(db.String(50), nullable=False)

    # Severite: critical, high, medium, low
    severity = db.Column(db.String(20), nullable=False)

    # Fichier JS source
    source_url = db.Column(db.String(1000), nullable=False)

    # Secret trouve (masque partiel pour affichage)
    secret_value = db.Column(db.Text, nullable=False)
    secret_preview = db.Column(db.String(200), nullable=True)

    # Contexte (ligne de code autour)
    context = db.Column(db.Text, nullable=True)

    # Description
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<JsSecret {self.secret_type} in {self.source_url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'secret_type': self.secret_type,
            'severity': self.severity,
            'source_url': self.source_url,
            'secret_value': self.secret_value,
            'secret_preview': self.secret_preview,
            'context': self.context,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InvestigationFile(db.Model):
    """Fichier partage dans une enquete"""
    __tablename__ = 'investigation_files'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation avec l'uploader
    uploaded_by = db.relationship('User', backref='uploaded_files')

    def __repr__(self):
        return f'<InvestigationFile {self.original_filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_by': self.uploaded_by.to_dict() if self.uploaded_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

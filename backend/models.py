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
    network_scans = db.relationship('NetworkScan', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    ad_scans = db.relationship('ADScan', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')
    bloodhound_analyses = db.relationship('BloodHoundAnalysis', backref='investigation', lazy='dynamic', cascade='all, delete-orphan')

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


# ============================================================================
# MODELES NETWORK (Scan reseau)
# ============================================================================

class NetworkScan(db.Model):
    """Scan reseau (ports, ping sweep)"""
    __tablename__ = 'network_scans'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Cible du scan
    target = db.Column(db.String(500), nullable=False)

    # Type: quick, full, all (pour portscan) ou pingsweep
    scan_type = db.Column(db.String(50), default='quick')
    scan_mode = db.Column(db.String(50), default='portscan')  # portscan, pingsweep

    # Status: pending, running, completed, failed
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)

    # Progress
    progress_current = db.Column(db.Integer, default=0)
    progress_total = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relations
    started_by = db.relationship('User', backref='started_network_scans')
    results = db.relationship('NetworkResult', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<NetworkScan {self.id} - {self.target}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'target': self.target,
            'scan_type': self.scan_type,
            'scan_mode': self.scan_mode,
            'status': self.status,
            'error_message': self.error_message,
            'progress_current': self.progress_current,
            'progress_total': self.progress_total,
            'started_by': self.started_by.to_dict() if self.started_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results_count': self.results.count()
        }


class NetworkResult(db.Model):
    """Resultat de scan reseau (port ouvert, hote actif)"""
    __tablename__ = 'network_results'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('network_scans.id'), nullable=False)

    # Infos hote
    ip = db.Column(db.String(50), nullable=False)
    hostname = db.Column(db.String(255), nullable=True)

    # Infos port (pour portscan)
    port = db.Column(db.Integer, nullable=True)
    protocol = db.Column(db.String(10), default='tcp')
    state = db.Column(db.String(20), default='open')
    service = db.Column(db.String(100), nullable=True)
    banner = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NetworkResult {self.ip}:{self.port}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'ip': self.ip,
            'hostname': self.hostname,
            'port': self.port,
            'protocol': self.protocol,
            'state': self.state,
            'service': self.service,
            'banner': self.banner
        }


# ============================================================================
# MODELES ACTIVE DIRECTORY
# ============================================================================

class ADScan(db.Model):
    """Scan Active Directory"""
    __tablename__ = 'ad_scans'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Cible du scan (DC)
    target = db.Column(db.String(500), nullable=False)
    domain = db.Column(db.String(255), nullable=True)

    # Type: basic, full
    scan_type = db.Column(db.String(50), default='basic')

    # Status: pending, running, completed, failed
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)

    # Progress
    progress_current = db.Column(db.Integer, default=0)
    progress_total = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relations
    started_by = db.relationship('User', backref='started_ad_scans')
    results = db.relationship('ADResult', backref='scan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ADScan {self.id} - {self.target}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'target': self.target,
            'domain': self.domain,
            'scan_type': self.scan_type,
            'status': self.status,
            'error_message': self.error_message,
            'progress_current': self.progress_current,
            'progress_total': self.progress_total,
            'started_by': self.started_by.to_dict() if self.started_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results_count': self.results.count()
        }


class ADResult(db.Model):
    """Resultat de scan Active Directory"""
    __tablename__ = 'ad_results'

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('ad_scans.id'), nullable=False)

    # Type: port, ldap_info, user, group, vulnerability, detection, etc.
    result_type = db.Column(db.String(50), nullable=False)

    # Nom (ex: "Domain Admins", "LDAP Anonymous Bind")
    name = db.Column(db.String(255), nullable=False)

    # Valeur
    value = db.Column(db.Text, nullable=True)

    # Severite: critical, high, medium, low, info
    severity = db.Column(db.String(20), default='info')

    # Port/Service (si applicable)
    port = db.Column(db.Integer, nullable=True)
    service = db.Column(db.String(100), nullable=True)

    # Description
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ADResult {self.result_type}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scan_id': self.scan_id,
            'result_type': self.result_type,
            'name': self.name,
            'value': self.value,
            'severity': self.severity,
            'port': self.port,
            'service': self.service,
            'description': self.description
        }


# ============================================================================
# MODELES BLOODHOUND ANALYSIS
# ============================================================================

class BloodHoundAnalysis(db.Model):
    """Analyse de fichiers BloodHound"""
    __tablename__ = 'bloodhound_analyses'

    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigations.id'), nullable=False)
    started_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Nom de l'analyse
    name = db.Column(db.String(255), nullable=True)

    # Domaine detecte
    domain = db.Column(db.String(255), nullable=True)

    # Methode d'analyse: 'native' (parser JSON) ou 'neo4j_adminer' (Neo4j + AD-Miner)
    analysis_method = db.Column(db.String(20), default='native')

    # Neo4j integration
    neo4j_imported = db.Column(db.Boolean, default=False)
    neo4j_uri = db.Column(db.String(255), nullable=True)

    # AD-Miner integration
    adminer_executed = db.Column(db.Boolean, default=False)
    adminer_report_path = db.Column(db.String(500), nullable=True)

    # Statistiques
    users_count = db.Column(db.Integer, default=0)
    computers_count = db.Column(db.Integer, default=0)
    groups_count = db.Column(db.Integer, default=0)
    domains_count = db.Column(db.Integer, default=0)

    # Status: pending, running, completed, failed
    status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relations
    started_by = db.relationship('User', backref='bloodhound_analyses')
    findings = db.relationship('BloodHoundFinding', backref='analysis', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('BloodHoundFile', backref='analysis', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<BloodHoundAnalysis {self.id} - {self.domain}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investigation_id': self.investigation_id,
            'name': self.name,
            'domain': self.domain,
            'analysis_method': self.analysis_method,
            'neo4j_imported': self.neo4j_imported,
            'neo4j_uri': self.neo4j_uri,
            'adminer_executed': self.adminer_executed,
            'adminer_report_path': self.adminer_report_path,
            'users_count': self.users_count,
            'computers_count': self.computers_count,
            'groups_count': self.groups_count,
            'domains_count': self.domains_count,
            'status': self.status,
            'error_message': self.error_message,
            'started_by': self.started_by.to_dict() if self.started_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'findings_count': self.findings.count(),
            'files_count': self.files.count()
        }


class BloodHoundFile(db.Model):
    """Fichier BloodHound uploade"""
    __tablename__ = 'bloodhound_files'

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('bloodhound_analyses.id'), nullable=False)

    # Infos fichier
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)

    # Type: users, computers, groups, domains, sessions, ous, gpos, containers
    file_type = db.Column(db.String(50), nullable=True)

    # Nombre d'objets dans le fichier
    objects_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BloodHoundFile {self.original_filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'objects_count': self.objects_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BloodHoundFinding(db.Model):
    """Resultat d'analyse BloodHound (vulnerabilite AD)"""
    __tablename__ = 'bloodhound_findings'

    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('bloodhound_analyses.id'), nullable=False)

    # Categorie: path_to_da, kerberoast, asreproast, delegation, acl_abuse, etc.
    category = db.Column(db.String(50), nullable=False)

    # Severite: critical, high, medium, low, info
    severity = db.Column(db.String(20), nullable=False)

    # Titre du finding
    title = db.Column(db.String(255), nullable=False)

    # Description detaillee
    description = db.Column(db.Text, nullable=True)

    # Objets impliques (JSON: source, target, relation)
    affected_objects = db.Column(db.JSON, nullable=True)

    # Chemin d'attaque (si applicable)
    attack_path = db.Column(db.JSON, nullable=True)

    # Recommandation
    recommendation = db.Column(db.Text, nullable=True)

    # References (MITRE, etc.)
    references = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BloodHoundFinding {self.category}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'category': self.category,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'affected_objects': self.affected_objects,
            'attack_path': self.attack_path,
            'recommendation': self.recommendation,
            'references': self.references,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

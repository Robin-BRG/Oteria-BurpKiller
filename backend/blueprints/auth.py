# -*- coding: utf-8 -*-
"""
Routes d'authentification
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User
from logger_config import get_logger, log_security_event
import re

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Logger pour ce module
logger = get_logger('auth')

def is_valid_email(email):
    """Validation basique d'email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """Inscription - equivalent a users#create en Rails"""
    try:
        data = request.get_json()
        
        # Validation
        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not email or not username or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        # Verifier si l'utilisateur existe deja
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Creer l'utilisateur
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(email=email, username=username, password_hash=password_hash)

        db.session.add(user)
        db.session.commit()

        logger.info(f'New user registered: {username} ({email})')
        log_security_event(logger, 'user_registration', user.id, f'Username: {username}', severity='info')

        # Connexion automatique apres inscription
        login_user(user)

        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f'Registration failed for {username}: {str(e)}')
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Connexion - equivalent a sessions#create en Rails"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Trouver l'utilisateur
        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            logger.warning(f'Failed login attempt for email: {email} from IP: {request.remote_addr}')
            log_security_event(logger, 'login_failure', 'unknown', f'Email: {email}', severity='warning')
            return jsonify({'error': 'Invalid email or password'}), 401

        # Connexion
        login_user(user)
        logger.info(f'User logged in: {user.username} (ID: {user.id})')
        log_security_event(logger, 'login_success', user.id, f'Username: {user.username}', severity='info')

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Deconnexion - equivalent a sessions#destroy en Rails"""
    user_id = current_user.id
    username = current_user.username
    logout_user()
    logger.info(f'User logged out: {username} (ID: {user_id})')
    log_security_event(logger, 'logout', user_id, f'Username: {username}', severity='info')
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    """Obtenir l'utilisateur connecte"""
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Verifier si l'utilisateur est connecte"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    return jsonify({'authenticated': False}), 200

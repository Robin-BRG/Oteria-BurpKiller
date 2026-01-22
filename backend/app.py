# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Configuration du logging
from logger_config import app_logger, get_logger

logger = get_logger('app')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# CORS avec credentials
CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://192.168.208.79:5173'])

logger.info('Flask application initialized')
logger.debug(f'Database URI: {app.config["SQLALCHEMY_DATABASE_URI"]}')


# Middleware pour logger toutes les requetes HTTP
@app.before_request
def log_request():
    """Log chaque requete entrante"""
    g.start_time = time.time()

    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    logger.debug(f'Request: {request.method} {request.path} - User: {user_id} - IP: {request.remote_addr}')


@app.after_request
def log_response(response):
    """Log la reponse de chaque requete"""
    if hasattr(g, 'start_time'):
        duration = round((time.time() - g.start_time) * 1000, 2)  # en ms
        user_id = current_user.id if current_user.is_authenticated else 'anonymous'

        log_msg = f'Response: {request.method} {request.path} - Status: {response.status_code} - Duration: {duration}ms - User: {user_id}'

        if response.status_code >= 500:
            logger.error(log_msg)
        elif response.status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    return response

from models import db, User
from auth import auth_bp, bcrypt
from investigations import investigations_bp
from recon import recon_bp
from enumeration import enum_bp
from http_tools import http_bp
from vulns import vulns_bp
from network import network_bp
from ad import ad_bp
from reports import reports_bp

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Non authentifie'}), 401

app.register_blueprint(auth_bp)
app.register_blueprint(investigations_bp)
app.register_blueprint(recon_bp)
app.register_blueprint(enum_bp)
app.register_blueprint(http_bp)
app.register_blueprint(vulns_bp)
app.register_blueprint(network_bp)
app.register_blueprint(ad_bp)
app.register_blueprint(reports_bp)

@app.route('/api/health', methods=['GET'])
def health():
    logger.debug('Health check requested')
    return jsonify({'status': 'ok', 'message': 'Backend Flask est operationnel'})


# Gestionnaire d'erreurs global
@app.errorhandler(Exception)
def handle_exception(error):
    """Log et gere les exceptions non capturees"""
    logger.exception(f'Unhandled exception: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info('Starting Flask development server on 0.0.0.0:5000')
    logger.warning('Debug mode is enabled - NOT for production use!')
    app.run(debug=True, host="0.0.0.0", port=5000)

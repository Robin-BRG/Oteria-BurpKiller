# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

from models import db, User
from auth import auth_bp, bcrypt
from investigations import investigations_bp
from recon import recon_bp
from enumeration import enum_bp
from http_tools import http_bp
from vulns import vulns_bp

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'error': 'Non authentifie'}), 401

app.register_blueprint(auth_bp)
app.register_blueprint(investigations_bp)
app.register_blueprint(recon_bp)
app.register_blueprint(enum_bp)
app.register_blueprint(http_bp)
app.register_blueprint(vulns_bp)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Backend Flask est operationnel'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

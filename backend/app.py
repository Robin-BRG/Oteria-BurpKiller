from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv
import subprocess
import sys
import os
import tempfile
import json
import glob
import re
import warnings

# Charger les variables d'environnement
load_dotenv()

# Ignorer les DeprecationWarnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///oteria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# CORS avec credentials
CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

# Initialiser les extensions
from models import db, User
from auth import auth_bp, bcrypt

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enregistrer les routes d'auth
app.register_blueprint(auth_bp)

# Dossier contenant les scripts
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')

def load_scripts_from_folder():
    """Charge automatiquement tous les scripts du dossier scripts/"""
    scripts = []
    script_files = glob.glob(os.path.join(SCRIPTS_DIR, '*.py'))
    
    for idx, script_path in enumerate(sorted(script_files), 1):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraire les métadonnées du docstring
            docstring_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            
            if docstring_match:
                docstring = docstring_match.group(1)
                name_match = re.search(r'name:\s*(.+)', docstring)
                desc_match = re.search(r'description:\s*(.+)', docstring)
                category_match = re.search(r'category:\s*(.+)', docstring)
                
                name = name_match.group(1).strip() if name_match else os.path.basename(script_path)
                description = desc_match.group(1).strip() if desc_match else "Aucune description"
                category = category_match.group(1).strip() if category_match else "Autre"
            else:
                name = os.path.basename(script_path).replace('.py', '').replace('_', ' ').title()
                description = "Script Python"
                category = "Autre"
            
            scripts.append({
                'id': idx,
                'name': name,
                'description': description,
                'category': category,
                'filename': os.path.basename(script_path),
                'code': content
            })
        
        except Exception as e:
            print(f"Erreur lors du chargement de {script_path}: {e}")
            continue
    
    return scripts

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint pour vérifier que le serveur fonctionne"""
    return jsonify({
        'status': 'ok',
        'message': 'Backend Flask est opérationnel'
    })

@app.route('/api/execute', methods=['POST'])
def execute_script():
    """Exécute un script Python fourni par l'utilisateur"""
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'Aucun code fourni'
            }), 400
        
        code = data['code']
        
        # Créer un fichier temporaire pour le script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            # Ajouter l'en-tête UTF-8
            f.write('# -*- coding: utf-8 -*-\n')
            f.write(code)
            temp_file = f.name
        
        try:
            # Exécuter le script Python
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30  # Timeout de 30 secondes
            )
            
            return jsonify({
                'success': True,
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode
            })
        
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Le script a dépassé le délai d\'exécution (30 secondes)'
        }), 408
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scripts', methods=['GET'])
def list_scripts():
    """Liste les scripts Python disponibles depuis le dossier scripts/"""
    scripts = load_scripts_from_folder()
    return jsonify(scripts)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# Oteria BurpKiller

Application web collaborative de tests de sécurité pour l'apprentissage de la cybersécurité. Alternative légère à Burp Suite développée dans le cadre d'un cours de Python cybersécurité.

## Fonctionnalités

### Reconnaissance
- Scanner HTTP de découverte de paths (wordlist customisable)
- Visualisation en graphe interactif des résultats
- Support des modes: stealth, normal, aggressive
- Progression en temps réel

### Enumération
- Détection automatique des technologies (serveur, framework, CMS)
- Analyse des headers HTTP de sécurité
- Évaluation du niveau de sécurité

### Exploitation
- Scanner SQL Injection (error-based, boolean-based, time-based, UNION)
- Scanner XSS (reflected, avec détection de filtres)
- Analyse JavaScript pour détecter les secrets exposés:
  - Google API Keys
  - AWS Access Keys
  - Stripe Keys
  - GitHub Tokens
  - JWT Tokens
  - API Keys génériques
  - Endpoints API cachés
- Request Builder HTTP (comme Burp Repeater)
- Historique des requêtes HTTP avec replay

### Collaboration
- Enquêtes collaboratives multi-utilisateurs
- Système d'authentification (register/login)
- Partage de fichiers entre membres
- Gestion des permissions (viewer, editor, admin)

## Stack Technique

### Backend
- Flask (Python 3.x)
- SQLAlchemy ORM
- Flask-Login pour l'authentification
- BeautifulSoup4 pour le parsing HTML
- Requests pour les requêtes HTTP

### Frontend
- React + TypeScript
- Vite (build tool)
- React Router pour la navigation
- React Flow pour la visualisation de graphes

## Installation

### Prérequis
- Python 3.8+
- Node.js 16+
- Git

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

Initialiser la base de données:
```python
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

Lancer le serveur:
```bash
python app.py
```

Le backend sera accessible sur http://localhost:5000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Le frontend sera accessible sur http://localhost:5173

## Utilisation

### 1. Créer un compte
- Accéder à http://localhost:5173
- S'enregistrer avec email/username/password

### 2. Créer une investigation
- Cliquer sur "Nouvelle Investigation"
- Renseigner le nom et l'URL cible
- Définir si l'investigation est publique/collaborative

### 3. Lancer des scans

**Reconnaissance:**
- Onglet "Reconnaissance"
- Choisir un mode de scan (stealth/normal/aggressive)
- Sélectionner une wordlist
- Lancer le scan
- Visualiser les résultats en graphe ou liste

**Enumération:**
- Onglet "Enumeration"
- Cliquer sur "Lancer le scan"
- Consulter les technologies détectées et headers de sécurité

**Exploitation:**
- Onglet "Exploitation"
- Scanner SQLi, XSS ou scan complet
- Scanner JavaScript pour les secrets
- Utiliser le Request Builder pour tester manuellement

## Architecture

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Home.tsx              # Page d'accueil
│   │   ├── Investigation.tsx     # Page principale d'une investigation
│   │   └── InvestigationsList.tsx
│   ├── components/
│   │   ├── ReconGraph.tsx        # Visualisation graphe reconnaissance
│   │   ├── ReconList.tsx         # Liste des résultats recon
│   │   ├── EnumDisplay.tsx       # Affichage enumération
│   │   ├── VulnDisplay.tsx       # Affichage vulnérabilités
│   │   ├── RequestBuilder.tsx    # Builder requêtes HTTP
│   │   └── HttpHistory.tsx       # Historique HTTP
│   └── context/
│       └── AuthContext.tsx       # Gestion authentification

backend/
├── app.py                        # Orchestrateur principal
├── models.py                     # Modèles SQLAlchemy
├── auth.py                       # Blueprint authentification
├── investigations.py             # Blueprint investigations
├── recon.py                      # Blueprint reconnaissance
├── enumeration.py                # Blueprint enumération
├── vulns.py                      # Blueprint vulnérabilités
├── http_tools.py                 # Blueprint HTTP tools
└── scripts/
    ├── http_scanner.py           # Scanner de paths HTTP
    ├── tech_detector.py          # Détection de technologies
    ├── sqli_scanner.py           # Scanner SQL Injection
    ├── xss_scanner.py            # Scanner XSS
    └── js_secret_scanner.py      # Scanner secrets JavaScript
```

## API Endpoints

### Authentication
- `POST /api/register` - Créer un compte
- `POST /api/login` - Se connecter
- `POST /api/logout` - Se déconnecter
- `GET /api/check-auth` - Vérifier l'authentification

### Investigations
- `GET /api/investigations` - Liste des investigations
- `POST /api/investigations` - Créer une investigation
- `GET /api/investigations/<id>` - Détails d'une investigation
- `PUT /api/investigations/<id>` - Modifier une investigation
- `DELETE /api/investigations/<id>` - Supprimer une investigation

### Reconnaissance
- `POST /api/investigations/<id>/scan` - Lancer un scan
- `GET /api/investigations/<id>/scans` - Liste des scans
- `GET /api/scans/<id>/results` - Résultats d'un scan

### Enumération
- `POST /api/investigations/<id>/enum` - Lancer scan enumération
- `GET /api/investigations/<id>/enum` - Résultats enumération

### Exploitation
- `POST /api/investigations/<id>/vuln-scan` - Lancer scan vulnérabilités
- `GET /api/investigations/<id>/vuln-scans` - Liste des scans vulns
- `GET /api/vuln-scans/<id>/results` - Résultats scan vulnérabilités
- `POST /api/investigations/<id>/js-scan` - Lancer scan JavaScript
- `GET /api/investigations/<id>/js-secrets` - Secrets JavaScript trouvés

### HTTP Tools
- `POST /api/investigations/<id>/http-requests` - Envoyer requête HTTP
- `GET /api/investigations/<id>/http-requests` - Historique requêtes
- `GET /api/http-requests/<id>` - Détails requête
- `DELETE /api/http-requests/<id>` - Supprimer requête

## Sécurité

**ATTENTION:** Cet outil est destiné à un usage éducatif uniquement.

- Ne testez JAMAIS des applications sans autorisation explicite
- Respectez les lois et réglementations en vigueur
- Utilisez uniquement sur vos propres applications ou avec permission écrite
- Les scans peuvent être détectés par les WAF et systèmes de sécurité

## Avertissement

Ce projet est développé dans un cadre pédagogique. Il n'est pas destiné à remplacer des outils professionnels comme Burp Suite, OWASP ZAP ou Acunetix. Les scanners sont basiques et peuvent produire des faux positifs.

## License

Projet éducatif - MIT License

## Auteurs

Robin BRG avec l'assistance de Claude Sonnet 4.5

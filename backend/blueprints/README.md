# Blueprints Flask

Ce dossier contient tous les blueprints (routes API) de l'application.

## Structure

Chaque fichier définit un blueprint Flask avec ses routes associées:

### Authentification et utilisateurs

**`auth.py`** - Blueprint `auth_bp`
- `POST /api/register` - Inscription
- `POST /api/login` - Connexion
- `POST /api/logout` - Déconnexion
- `GET /api/check-auth` - Vérification session
- `GET /api/me` - Informations utilisateur courant

### Gestion des investigations

**`investigations.py`** - Blueprint `investigations_bp`
- `GET /api/investigations` - Liste des investigations
- `POST /api/investigations` - Créer investigation
- `GET /api/investigations/:id` - Détails investigation
- `PUT /api/investigations/:id` - Modifier investigation
- `DELETE /api/investigations/:id` - Supprimer investigation
- `POST /api/investigations/:id/members` - Ajouter membre
- `GET /api/investigations/:id/members` - Liste membres
- `POST /api/investigations/:id/files` - Upload fichier
- `GET /api/investigations/:id/files` - Liste fichiers

### Modules de scan Web

**`recon.py`** - Blueprint `recon_bp`
- Reconnaissance HTTP (scan de paths)
- Utilise `scripts/recon/http_scanner.py`

**`enumeration.py`** - Blueprint `enum_bp`
- Énumération de technologies et headers HTTP
- Utilise `scripts/enum/tech_detector.py`

**`vulns.py`** - Blueprint `vulns_bp`
- Scan de vulnérabilités (SQLi, XSS, secrets JavaScript)
- Utilise `scripts/exploit/sqli_scanner.py`, `xss_scanner.py`, `js_secret_scanner.py`

**`http_tools.py`** - Blueprint `http_bp`
- Request Builder (équivalent Burp Repeater)
- Historique des requêtes HTTP

### Modules de scan Réseau et AD

**`network.py`** - Blueprint `network_bp`
- Scan de ports TCP
- Ping sweep
- Détection de services

**`ad.py`** - Blueprint `ad_bp`
- Détection de contrôleurs de domaine
- Énumération Active Directory
- Vérification LDAP, SMB, Kerberos

### Reporting

**`reports.py`** - Blueprint `reports_bp`
- `GET /api/investigations/:id/report/html` - Générer rapport HTML
- `GET /api/investigations/:id/report/pdf` - Télécharger rapport PDF
- `GET /api/investigations/:id/report/preview` - Aperçu données

**`report_generator.py`** - Module (pas un blueprint)
- Fonctions `generate_html_report()` et `generate_pdf_report()`
- Template Jinja2 pour génération HTML
- Utilisé par `reports.py`

## Convention de nommage

- Tous les blueprints se terminent par `_bp`
- Tous les blueprints utilisent le préfixe `/api`
- Les routes sont RESTful quand possible

## Import dans app.py

```python
from blueprints.auth import auth_bp, bcrypt
from blueprints.investigations import investigations_bp
from blueprints.recon import recon_bp
# etc...

app.register_blueprint(auth_bp)
app.register_blueprint(investigations_bp)
# etc...
```

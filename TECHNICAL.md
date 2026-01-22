# Documentation Technique - BurpKiller

Ce document decrit l'architecture interne du projet, les fichiers cles et le fonctionnement des differentes fonctionnalites.

---

## Architecture Generale

```
Frontend (React)          Backend (Flask)           Base de donnees
    |                          |                         |
    |   -- API REST -->        |                         |
    |   <-- JSON --            |   -- SQLAlchemy -->     |
    |                          |                         |
Port 5173                  Port 5000                  SQLite
```

---

## Backend (Python/Flask)

### Point d'entree

**Fichier: `backend/app.py`**

- Initialisation de l'application Flask
- Configuration CORS et sessions
- Enregistrement des Blueprints (modules)
- Gestion du user loader pour Flask-Login
- Creation des tables au demarrage

```python
# Blueprints enregistres
app.register_blueprint(auth_bp)           # /api/register, /api/login, etc.
app.register_blueprint(investigations_bp) # /api/investigations
app.register_blueprint(recon_bp)          # /api/investigations/:id/scans
app.register_blueprint(enum_bp)           # /api/investigations/:id/enum
app.register_blueprint(vulns_bp)          # /api/investigations/:id/vuln-scan
app.register_blueprint(http_tools_bp)     # /api/investigations/:id/http-requests
app.register_blueprint(network_bp)        # /api/investigations/:id/network-scans
app.register_blueprint(ad_bp)             # /api/investigations/:id/ad-scans
```

---

### Modeles de donnees

**Fichier: `backend/models.py`**

| Modele | Description | Relations |
|--------|-------------|-----------|
| `User` | Utilisateur avec authentification | owns investigations, memberships |
| `Investigation` | Enquete/projet de pentest | owner, members, scans |
| `InvestigationMember` | Relation N:M user-investigation | user_id, investigation_id, role |
| `InvestigationFile` | Fichiers uploades | investigation_id |
| `ReconScan` | Scan de reconnaissance HTTP | investigation_id, results |
| `ReconResult` | Resultat d'un path trouve | scan_id |
| `EnumScan` | Scan d'enumeration tech | investigation_id |
| `EnumResult` | Technologies detectees | scan_id |
| `NetworkScan` | Scan de ports reseau | investigation_id |
| `NetworkResult` | Port ouvert trouve | scan_id |
| `ADScan` | Scan Active Directory | investigation_id |
| `ADResult` | Resultat AD (service, vuln) | scan_id |
| `VulnerabilityScan` | Scan SQLi/XSS | investigation_id |
| `Vulnerability` | Vulnerabilite trouvee | scan_id |
| `HttpRequest` | Requete HTTP enregistree | investigation_id |
| `JsSecret` | Secret JS detecte | investigation_id |

#### Methodes importantes des modeles

```python
# User
user.check_password(password)  # Verification bcrypt

# Investigation
investigation.user_can_view(user)   # Peut voir (owner, member, public)
investigation.user_can_edit(user)   # Peut editer (owner, editor role)
investigation.to_dict()             # Serialisation JSON
```

---

### Modules Backend

#### 1. Authentification (`backend/auth.py`)

| Route | Methode | Fonction |
|-------|---------|----------|
| `/api/register` | POST | Creer un compte |
| `/api/login` | POST | Connexion (session) |
| `/api/logout` | POST | Deconnexion |
| `/api/check-auth` | GET | Verifier si connecte |
| `/api/me` | GET | Infos utilisateur courant |

**Securite:**
- Mots de passe hashes avec bcrypt
- Sessions Flask-Login
- Decorator `@login_required` sur routes protegees

---

#### 2. Investigations (`backend/investigations.py`)

| Route | Methode | Fonction |
|-------|---------|----------|
| `/api/investigations` | GET | Liste investigations accessibles |
| `/api/investigations` | POST | Creer investigation |
| `/api/investigations/:id` | GET | Details investigation |
| `/api/investigations/:id` | PUT | Modifier investigation |
| `/api/investigations/:id` | DELETE | Supprimer investigation |
| `/api/investigations/:id/members` | POST | Ajouter membre |
| `/api/investigations/:id/members` | GET | Lister membres |
| `/api/investigations/:id/files` | POST | Upload fichier |
| `/api/investigations/:id/files` | GET | Lister fichiers |

---

#### 3. Reconnaissance Web (`backend/recon.py`)

**Fonctionnement:**
1. Cree un `ReconScan` en base
2. Lance un thread en arriere-plan
3. Le thread appelle `http_scanner.scan_paths()`
4. Sauvegarde les `ReconResult` trouves
5. Met a jour le statut du scan

**Fichier scanner: `backend/scripts/http_scanner.py`**

```python
def scan_paths(base_url, wordlist, mode='normal', callback=None):
    # Modes: stealth (1 req/s), normal (5 req/s), aggressive (20 req/s)
    # Retourne liste de paths trouves avec status codes
```

---

#### 4. Enumeration (`backend/enumeration.py`)

**Fonctionnement:**
1. Analyse les headers HTTP de la cible
2. Detecte les technologies (serveur, framework, CMS)
3. Evalue la securite des headers

**Fichier scanner: `backend/scripts/tech_detector.py`**

```python
def detect_technologies(url):
    # Detecte: Server, X-Powered-By, frameworks JS, CMS
    # Retourne dict avec technologies et headers securite
```

---

#### 5. Scan Reseau (`backend/network.py`)

**Fonctionnement:**
1. Resout la cible (hostname -> IP)
2. Scanne les ports TCP avec sockets
3. Recupere les bannieres des services
4. Identifie les services par port

**Fonctions principales:**

```python
def scan_port(ip, port, timeout=2):
    # Retourne True si port ouvert

def grab_banner(ip, port, timeout=3):
    # Recupere banniere du service

def scan_network(target, scan_type='quick'):
    # scan_type: 'quick' (25 ports), 'full' (100+), 'all' (65535)

def ping_sweep(network):
    # Decouvre hotes actifs sur un /24
```

**Ports scannes (mode quick):**
21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995,
1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017

---

#### 6. Active Directory (`backend/ad.py`)

**Fonctionnement:**
1. Scanne les ports AD standards
2. Detecte si la cible est un DC
3. Teste l'acces LDAP anonyme
4. Verifie les sessions NULL SMB

**Fonctions principales:**

```python
def detect_domain_controller(target):
    # Score de confiance base sur ports AD ouverts
    # Retourne: is_dc, confidence, indicators

def check_ldap_anonymous(target):
    # Tente connexion LDAP anonyme

def check_smb_null_session(target):
    # Verifie sessions NULL SMB
```

**Ports AD:**
- 88: Kerberos
- 389: LDAP
- 636: LDAPS
- 445: SMB
- 3268: LDAP Global Catalog
- 9389: AD Web Services

---

#### 7. Vulnerabilites (`backend/vulns.py`)

**Scanners disponibles:**

| Type | Fichier | Detection |
|------|---------|-----------|
| SQLi | `scripts/sqli_scanner.py` | Error-based, Boolean-based |
| XSS | `scripts/xss_scanner.py` | Reflected XSS |
| JS Secrets | `scripts/js_secret_scanner.py` | API keys, tokens dans JS |

**Patterns JS detectes:**
- Google API Keys
- AWS Access/Secret Keys
- Stripe Keys (pk_live, sk_live)
- GitHub Tokens
- JWT Tokens
- Private Keys

---

#### 8. HTTP Tools (`backend/http_tools.py`)

**Request Builder:**
- Envoi requetes HTTP personnalisees
- Sauvegarde historique
- Replay de requetes

---

## Frontend (React/TypeScript)

### Structure des fichiers

```
frontend/src/
|-- App.tsx                    # Routeur principal
|-- index.css                  # Variables CSS globales
|-- main.tsx                   # Point d'entree React
|
|-- context/
|   |-- AuthContext.tsx        # Context authentification
|
|-- pages/
|   |-- Home.tsx               # Page d'accueil
|   |-- Login.tsx              # Connexion
|   |-- Register.tsx           # Inscription
|   |-- Investigation.tsx      # Page investigation (onglets)
|   |-- InvestigationsList.tsx # Liste investigations
|
|-- components/
    |-- ReconGraph.tsx         # Visualisation graphe React Flow
    |-- ReconList.tsx          # Liste resultats reconnaissance
    |-- EnumDisplay.tsx        # Affichage enumeration
    |-- NetworkDisplay.tsx     # Affichage scan reseau
    |-- ADDisplay.tsx          # Affichage scan AD
    |-- VulnDisplay.tsx        # Affichage vulnerabilites
    |-- RequestBuilder.tsx     # Builder requetes HTTP
    |-- HttpHistory.tsx        # Historique requetes
```

---

### Context d'authentification

**Fichier: `frontend/src/context/AuthContext.tsx`**

```typescript
interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
}
```

Usage dans composants:
```typescript
const { user, login, logout } = useAuth();
```

---

### Page Investigation

**Fichier: `frontend/src/pages/Investigation.tsx`**

Gere les onglets:
1. **Reconnaissance** - Scan de paths HTTP
2. **Enumeration** - Detection technologies
3. **Network** - Scan de ports
4. **Active Directory** - Enumeration AD
5. **Exploitation** - SQLi, XSS, JS Secrets
6. **Rapport** - Synthese (a implementer)

Chaque onglet charge son composant correspondant qui fait des appels API.

---

### Variables CSS

**Fichier: `frontend/src/index.css`**

```css
:root {
  /* Couleurs de fond */
  --bg-primary: #ffffff;
  --bg-secondary: #f6f8fa;
  --bg-tertiary: #f0f2f5;

  /* Couleurs de texte */
  --text-primary: #1f2328;
  --text-secondary: #656d76;
  --text-muted: #8b949e;

  /* Couleurs d'accent */
  --accent-primary: #0969da;    /* Bleu */
  --accent-success: #1a7f37;    /* Vert */
  --accent-warning: #9a6700;    /* Orange */
  --accent-error: #cf222e;      /* Rouge */

  /* Bordures */
  --border-color: #d0d7de;
}
```

---

## Flux de donnees typique

### Exemple: Lancement d'un scan reseau

```
1. Frontend: NetworkDisplay.tsx
   -> Clic bouton "Lancer scan"
   -> POST /api/investigations/:id/network-scans

2. Backend: network.py
   -> Cree NetworkScan en base (status: running)
   -> Lance thread en arriere-plan
   -> Retourne immediatement scan.to_dict()

3. Thread arriere-plan
   -> scan_network(target, scan_type)
   -> Pour chaque port ouvert: cree NetworkResult
   -> Met a jour scan.status = 'completed'

4. Frontend: Polling
   -> GET /api/network-scans/:id (toutes les 2s)
   -> Si status == 'completed':
      -> GET /api/network-scans/:id/results
      -> Affiche resultats
```

---

## Configuration

### Backend

**Variables d'environnement (optionnel):**
```
SECRET_KEY=votre_cle_secrete
DATABASE_URL=sqlite:///instance/app.db
```

**Configuration dans app.py:**
```python
app.config['SECRET_KEY'] = 'dev-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
```

### Frontend

**Fichier: `frontend/vite.config.ts`**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
  }
}
```

---

## Base de donnees

### Localisation
`backend/instance/app.db` (SQLite)

### Reinitialisation
```bash
cd backend
rm instance/app.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Inspection
```bash
sqlite3 backend/instance/app.db
.tables
.schema User
SELECT * FROM user;
```

---

## Securite implementee

| Mesure | Implementation |
|--------|----------------|
| Hash mots de passe | bcrypt via Flask-Bcrypt |
| Sessions | Flask-Login avec cookies HttpOnly |
| CORS | Flask-CORS avec credentials |
| Permissions | Verification owner/member sur chaque route |
| Upload fichiers | Whitelist extensions (.txt, .pdf, .png, etc.) |
| Validation | Verification des entrees avant traitement |

---

## Points d'extension

### Ajouter un nouveau module backend

1. Creer `backend/nouveau_module.py`
2. Creer Blueprint:
   ```python
   from flask import Blueprint
   nouveau_bp = Blueprint('nouveau', __name__)
   ```
3. Ajouter routes avec decorateurs
4. Enregistrer dans `app.py`:
   ```python
   from nouveau_module import nouveau_bp
   app.register_blueprint(nouveau_bp)
   ```

### Ajouter un nouvel onglet frontend

1. Creer `frontend/src/components/NouveauDisplay.tsx`
2. Dans `Investigation.tsx`:
   - Ajouter tab: `{ id: 'nouveau', label: 'Nouveau' }`
   - Ajouter case dans `renderTabContent()`
   - Importer le composant

---

## Commandes utiles

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm run dev

# Build production
npm run build
```

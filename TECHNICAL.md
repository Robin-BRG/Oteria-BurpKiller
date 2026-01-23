# Documentation Technique - BurpKiller

Ce document decrit l'architecture interne du projet, les fichiers cles et le fonctionnement des differentes fonctionnalites.

---

## Architecture Generale

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │     Backend     │     │   Base donnees  │
│     (React)     │────▶│     (Flask)     │────▶│    (SQLite)     │
│   Port 5173     │◀────│    Port 5000    │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │                       ▼
        │               ┌─────────────────┐
        │               │    Scripts      │
        │               │    (Python)     │
        │               └─────────────────┘
        │
        ▼
   Navigateur Web
```

---

## Structure des fichiers

```
backend/
├── app.py                    # Point d'entree Flask
├── models.py                 # Modeles SQLAlchemy
├── logger_config.py          # Configuration logging
│
├── blueprints/               # Modules API (routes)
│   ├── __init__.py
│   ├── auth.py               # Authentification
│   ├── investigations.py     # CRUD investigations
│   ├── recon.py              # Scan HTTP paths
│   ├── enumeration.py        # Detection technologies
│   ├── network.py            # Scan ports reseau
│   ├── ad.py                 # Enumeration Active Directory
│   ├── vulns.py              # Scan vulnerabilites
│   ├── http_tools.py         # Request builder
│   ├── reports.py            # Generation rapports
│   ├── report_generator.py   # Logique generation PDF/HTML
│   ├── terminal.py           # Terminal Python web
│   └── presence.py           # Suivi presence utilisateurs
│
├── scripts/                  # Scripts Python "purs"
│   ├── recon/
│   │   └── http_scanner.py   # Scanner de paths HTTP
│   ├── enum/
│   │   └── tech_detector.py  # Detection technologies
│   └── exploit/
│       ├── sqli_scanner.py   # Scanner SQLi
│       ├── xss_scanner.py    # Scanner XSS
│       └── js_secret_scanner.py
│
├── tests/                    # Tests unitaires (131 tests, 75% coverage)
│   ├── conftest.py           # Fixtures pytest
│   ├── test_auth.py
│   ├── test_investigations.py
│   ├── test_network.py
│   ├── test_reports.py
│   ├── test_ad.py
│   ├── test_recon.py
│   ├── test_enumeration.py
│   ├── test_vulns.py
│   ├── test_http_tools.py
│   ├── test_terminal.py
│   └── test_presence.py
│
└── instance/
    └── app.db                # Base SQLite

frontend/
├── src/
│   ├── App.tsx               # Routeur principal
│   ├── main.tsx              # Point d'entree
│   ├── index.css             # Variables CSS globales
│   │
│   ├── context/
│   │   └── AuthContext.tsx   # Context authentification
│   │
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Investigation.tsx # Page principale (onglets)
│   │   └── InvestigationsList.tsx
│   │
│   └── components/
│       ├── NetworkDisplay.tsx/.css
│       ├── ADDisplay.tsx/.css
│       ├── ReconGraph.tsx/.css
│       ├── EnumDisplay.tsx/.css
│       ├── VulnDisplay.tsx/.css
│       ├── RequestBuilder.tsx/.css
│       ├── ReportGenerator.tsx/.css
│       ├── TerminalTab.tsx/.css      # Terminal Python
│       ├── ActiveUsers.tsx/.css      # Utilisateurs actifs
│       └── Processes.tsx/.css        # Processus en cours
│
└── vite.config.ts            # Config Vite (proxy API)
```

---

## Comment les scripts Python sont charges

### Mecanisme d'import dynamique

Les scripts dans `scripts/` sont des modules Python independants.
Les blueprints les chargent via manipulation du `sys.path`:

**Fichier: `blueprints/recon.py` (lignes 12-15)**

```python
import sys
import os

# 1. Calcule le chemin absolu vers scripts/recon/
SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # backend/
    'scripts',
    'recon'
)

# 2. Ajoute au PYTHONPATH
sys.path.insert(0, SCRIPTS_DIR)

# 3. Importe les fonctions
from http_scanner import scan_http, COMMON_PATHS
```

### Pourquoi cette architecture ?

1. **Scripts executables independamment**:
   ```bash
   cd backend/scripts/recon
   python http_scanner.py https://example.com
   ```

2. **Pas de dependance Flask** dans les scripts
3. **Facile a tester** unitairement
4. **Reutilisable** dans d'autres projets

---

## Flux d'execution complet

### Exemple: Lancement d'un scan de reconnaissance

```
┌────────────────────────────────────────────────────────────────────────┐
│  ETAPE 1: Frontend envoie la requete                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  NetworkDisplay.tsx:                                                    │
│  const startScan = async () => {                                       │
│    const response = await fetch(                                       │
│      '/api/investigations/1/network-scans',                            │
│      {                                                                  │
│        method: 'POST',                                                  │
│        body: JSON.stringify({                                          │
│          target: '192.168.1.1',                                        │
│          scan_type: 'quick'                                            │
│        })                                                               │
│      }                                                                  │
│    );                                                                   │
│    const scan = await response.json();                                 │
│    setActiveScan(scan);  // { id: 1, status: 'running' }               │
│  }                                                                      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│  ETAPE 2: Backend recoit et lance le thread                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  blueprints/network.py:                                                │
│                                                                         │
│  @network_bp.route('/api/.../network-scans', methods=['POST'])         │
│  @login_required                                                        │
│  def start_network_scan(inv_id):                                       │
│      # 1. Cree l'entree en base                                        │
│      scan = NetworkScan(                                               │
│          target=data['target'],                                        │
│          status='running'                                              │
│      )                                                                  │
│      db.session.add(scan)                                              │
│      db.session.commit()                                               │
│                                                                         │
│      # 2. Lance le thread en arriere-plan                              │
│      thread = threading.Thread(                                        │
│          target=run_network_scan,                                      │
│          args=(app._get_current_object(), scan.id, ...)                │
│      )                                                                  │
│      thread.daemon = True                                              │
│      thread.start()                                                    │
│                                                                         │
│      # 3. Retourne IMMEDIATEMENT (non-bloquant)                        │
│      return jsonify(scan.to_dict()), 201                               │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
              ▼                                           ▼
┌─────────────────────────────┐         ┌─────────────────────────────────┐
│  THREAD PRINCIPAL           │         │  THREAD ARRIERE-PLAN             │
│  (Continue a repondre)      │         │  (Execute le scan)               │
├─────────────────────────────┤         ├─────────────────────────────────┤
│                             │         │                                  │
│  Retourne au frontend:      │         │  def run_network_scan(app, ...): │
│  { id: 1, status: running } │         │      with app.app_context():     │
│                             │         │          # Scan les ports        │
│                             │         │          for port in PORTS:      │
│                             │         │              if is_open(ip, port):│
│                             │         │                  save_result()   │
│                             │         │                                  │
│                             │         │          scan.status = 'completed'│
│                             │         │          db.session.commit()     │
│                             │         │                                  │
└─────────────────────────────┘         └─────────────────────────────────┘
              │                                           │
              ▼                                           │
┌─────────────────────────────┐                           │
│  ETAPE 3: Frontend poll     │                           │
├─────────────────────────────┤                           │
│                             │                           │
│  useEffect(() => {          │                           │
│    if (activeScan) {        │                           │
│      setInterval(() => {    │◀──────────────────────────┘
│        checkStatus()        │    Quand termine, le frontend
│      }, 2000)               │    detecte status='completed'
│    }                        │
│  })                         │
│                             │
└─────────────────────────────┘
```

---

## Le contexte Flask dans les threads

### Probleme

Flask utilise un "contexte d'application" pour acceder a `db`, `current_user`, etc.
Ce contexte n'existe que dans le thread principal.

### Solution

Chaque thread doit creer son propre contexte:

```python
def run_scan_task(scan_id, target_url):
    from app import app  # Import ici, pas en haut du fichier

    with app.app_context():  # Cree le contexte pour ce thread
        scan = db.session.get(NetworkScan, scan_id)

        # Maintenant on peut utiliser db.session
        results = do_scan(target_url)

        for result in results:
            db.session.add(NetworkResult(...))

        scan.status = 'completed'
        db.session.commit()
```

**Pourquoi `from app import app` dans la fonction ?**

Pour eviter les imports circulaires:
- `app.py` importe `blueprints/network.py`
- `network.py` ne peut pas importer `app` au niveau module

---

## Routes API principales

### Authentification (`/api/auth`)

| Route | Methode | Description |
|-------|---------|-------------|
| `/api/register` | POST | Creer compte |
| `/api/login` | POST | Connexion |
| `/api/logout` | POST | Deconnexion |
| `/api/check-auth` | GET | Verifier session |
| `/api/me` | GET | Info utilisateur |

### Investigations (`/api/investigations`)

| Route | Methode | Description |
|-------|---------|-------------|
| `/api/investigations` | GET | Liste |
| `/api/investigations` | POST | Creer |
| `/api/investigations/:id` | GET | Details |
| `/api/investigations/:id` | PUT | Modifier |
| `/api/investigations/:id` | DELETE | Supprimer |

### Scans (par investigation)

| Route | Description |
|-------|-------------|
| `POST /api/investigations/:id/scans` | Lance scan HTTP |
| `POST /api/investigations/:id/network-scans` | Lance scan ports |
| `POST /api/investigations/:id/ad-scans` | Lance scan AD |
| `POST /api/investigations/:id/enum` | Lance enumeration |
| `POST /api/investigations/:id/vuln-scan` | Lance scan vulns |

### Resultats

| Route | Description |
|-------|-------------|
| `GET /api/scans/:id` | Statut d'un scan |
| `GET /api/scans/:id/results` | Resultats d'un scan |
| `GET /api/network-scans/:id/results` | Resultats scan reseau |

---

## Modeles de donnees

### Relations

```
User (1) ───────────────┐
  │                     │
  │ owns                │ member_of
  ▼                     ▼
Investigation ◀─── InvestigationMember
  │
  │ has_many
  ▼
┌─────────────────────────────────────┐
│  ReconScan      → ReconResult       │
│  EnumScan       → EnumResult        │
│  NetworkScan    → NetworkResult     │
│  ADScan         → ADResult          │
│  VulnerabilityScan → Vulnerability  │
│  HttpRequest                        │
│  JsSecret                           │
└─────────────────────────────────────┘
```

### Serialisation JSON

Chaque modele a une methode `to_dict()`:

```python
class NetworkScan(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'target': self.target,
            'status': self.status,
            'progress_current': self.progress_current,
            'progress_total': self.progress_total,
            'results_count': self.results.count(),
            'created_at': self.created_at.isoformat(),
            ...
        }
```

---

## Frontend: Communication avec l'API

### Appels API avec credentials

```typescript
// Toujours inclure credentials pour les cookies de session
const response = await fetch('/api/investigations', {
  credentials: 'include',  // IMPORTANT
  headers: { 'Content-Type': 'application/json' }
});
```

### Proxy Vite

Le frontend tourne sur `:5173`, le backend sur `:5000`.
Vite proxy les requetes `/api/*`:

**vite.config.ts:**
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  }
}
```

### Polling pour les scans

```typescript
useEffect(() => {
  if (activeScan?.status === 'running') {
    const interval = setInterval(() => {
      // Verifie le statut toutes les 2 secondes
      fetch(`/api/network-scans/${activeScan.id}`)
        .then(r => r.json())
        .then(scan => {
          if (scan.status === 'completed') {
            loadResults(scan.id);
            clearInterval(interval);
          }
        });
    }, 2000);

    return () => clearInterval(interval);
  }
}, [activeScan]);
```

---

## Ajouter une nouvelle fonctionnalite

### 1. Creer le script Python

```python
# backend/scripts/nouveau/mon_scanner.py

def scan_something(target, options):
    """Script sans dependance Flask"""
    results = []
    # ... logique de scan ...
    return results

if __name__ == '__main__':
    # Executable directement pour tests
    import sys
    target = sys.argv[1]
    print(scan_something(target, {}))
```

### 2. Creer le blueprint

```python
# backend/blueprints/nouveau.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation
import threading
import sys
import os

nouveau_bp = Blueprint('nouveau', __name__)

# Charger le script
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'nouveau')
sys.path.insert(0, SCRIPTS_DIR)
from mon_scanner import scan_something

@nouveau_bp.route('/api/investigations/<int:inv_id>/nouveau-scan', methods=['POST'])
@login_required
def start_scan(inv_id):
    # ... creer scan en DB, lancer thread ...
    pass
```

### 3. Enregistrer dans app.py

```python
from blueprints.nouveau import nouveau_bp
app.register_blueprint(nouveau_bp)
```

### 4. Creer le composant React

```typescript
// frontend/src/components/NouveauDisplay.tsx

function NouveauDisplay({ investigationId }) {
  const startScan = async () => {
    await fetch(`/api/investigations/${investigationId}/nouveau-scan`, {
      method: 'POST',
      credentials: 'include'
    });
  };

  return <button onClick={startScan}>Lancer</button>;
}
```

### 5. Ajouter l'onglet

```typescript
// frontend/src/pages/Investigation.tsx

const tabs = [
  // ... autres onglets ...
  { id: 'nouveau', label: 'Nouveau' }
];

const renderTabContent = () => {
  switch (activeTab) {
    case 'nouveau':
      return <NouveauDisplay investigationId={id} />;
  }
};
```

---

## Commandes utiles

```bash
# Demarrer le developpement
cd backend && python app.py
cd frontend && npm run dev

# Reset la base de donnees
cd backend
rm instance/app.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Lancer les tests
cd backend
python -m pytest tests/ -v

# Build production
cd frontend && npm run build
```

---

## Variables d'environnement

```bash
# backend/.env (optionnel)
SECRET_KEY=votre_cle_secrete_production
DATABASE_URL=sqlite:///instance/app.db
```

---

## Securite

| Mesure | Implementation |
|--------|----------------|
| Mots de passe | Hashes bcrypt |
| Sessions | Cookies HttpOnly, SameSite=Lax |
| CORS | Origins whitelist |
| Permissions | Verification owner/member par route |
| Inputs | Validation cote serveur |
| SQL | ORM SQLAlchemy (pas de raw SQL) |

---

## Module Terminal

Le module Terminal permet d'executer du code Python directement depuis l'interface web.

### Architecture

```
Frontend (TerminalTab.tsx)
    │
    ▼ POST /api/terminal/execute
    │  { code: "...", timeout: 10 }
    │
Backend (terminal.py)
    │
    ├─► Cree fichier temporaire (.py)
    ├─► Lance subprocess Python
    ├─► Capture stdout/stderr
    └─► Retourne resultat JSON
```

### Securite du Terminal

- Timeout configurable (max 30s)
- Fichiers temporaires supprimes apres execution
- Authentification requise
- Processus enregistre dans le systeme de presence

### Exemple de requete

```bash
curl -X POST http://localhost:5000/api/terminal/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(2+2)", "timeout": 5}'
```

Reponse:
```json
{
  "stdout": "4\n",
  "stderr": "",
  "returncode": 0,
  "timeout": false
}
```

---

## Module Presence

Le module Presence permet de suivre les utilisateurs connectes et les processus en cours.

### Fonctionnement

```
┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │     Backend     │
│                 │     │                 │
│  useEffect()    │────▶│  /heartbeat     │
│  interval 30s   │     │                 │
│                 │     │  _active_users  │
│  ActiveUsers    │◀────│  (in-memory)    │
│  Processes      │     │  _processes     │
└─────────────────┘     └─────────────────┘
```

### Heartbeat

Le frontend envoie un heartbeat toutes les 30 secondes pour signaler sa presence:

```javascript
// Investigation.tsx
useEffect(() => {
  const sendHeartbeat = async () => {
    await fetch('/api/presence/heartbeat', {
      method: 'POST',
      body: JSON.stringify({ page: `investigation/${id}` })
    });
  };

  sendHeartbeat();
  const interval = setInterval(sendHeartbeat, 30000);
  return () => clearInterval(interval);
}, [id]);
```

### Nettoyage automatique

Un thread de nettoyage tourne en arriere-plan:
- Utilisateurs inactifs depuis 90s → supprimes
- Processus termines depuis 5min → supprimes

### Routes API

| Route | Description |
|-------|-------------|
| `POST /api/presence/heartbeat` | Signaler presence |
| `GET /api/presence/active` | Liste utilisateurs actifs |
| `GET /api/processes` | Liste processus en cours |
| `GET /api/presence/stats` | Statistiques |

### Fonctions utilitaires (pour autres modules)

```python
from blueprints.presence import start_process, stop_process

# Enregistrer un processus
pid = start_process('scan', 'Scan de ports', owner='user1')

# Terminer un processus
stop_process(pid, status='completed')
```

# 🏗️ Architecture du Projet Oteria Python

## 📊 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        NAVIGATEUR WEB                            │
│                    http://localhost:5173                         │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    FRONTEND (React)                        │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │   Sidebar   │  │   Editeur    │  │   Affichage     │  │  │
│  │  │   Scripts   │  │     Code     │  │   Resultats     │  │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/JSON (API REST)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    BACKEND (Flask Python)                        │
│                    http://localhost:5000                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      app.py (Orchestrateur)                 │ │
│  │                                                              │ │
│  │  Routes API:                                                │ │
│  │  • GET  /api/health     → Status du serveur                │ │
│  │  • GET  /api/scripts    → Liste des scripts disponibles    │ │
│  │  • POST /api/execute    → Execute un script Python         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            │                                      │
│                            │ load_scripts_from_folder()          │
│                            ▼                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Dossier scripts/                               │ │
│  │                                                              │ │
│  │  • hello_world.py        (chargé automatiquement)          │ │
│  │  • calculs.py            (chargé automatiquement)          │ │
│  │  • boucles.py            (chargé automatiquement)          │ │
│  │  • listes.py             (chargé automatiquement)          │ │
│  │  • fibonacci.py          (chargé automatiquement)          │ │
│  │  • dictionnaires.py      (chargé automatiquement)          │ │
│  │  • exemple_complet.py    (chargé automatiquement)          │ │
│  │  • ...vos_scripts.py     (ajoutez les vôtres!)            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux de Données

### 1️⃣ Chargement des Scripts

```
Au démarrage du backend:
1. Flask démarre
2. app.py scanne le dossier scripts/
3. Pour chaque fichier .py:
   - Lecture du fichier
   - Extraction des métadonnées (docstring)
   - Stockage en mémoire
4. API /api/scripts prête
```

### 2️⃣ Affichage dans l'Interface

```
Quand l'utilisateur ouvre la page web:
1. Frontend React se charge
2. Appel GET /api/health → Vérifie que le backend est connecté
3. Appel GET /api/scripts → Récupère la liste des scripts
4. Affichage des scripts dans la sidebar avec catégories
```

### 3️⃣ Exécution d'un Script

```
Quand l'utilisateur clique sur "Exécuter":
1. Frontend récupère le code de l'éditeur
2. POST /api/execute avec {code: "print('hello')"}
3. Backend reçoit le code
4. Création d'un fichier temporaire avec:
   - En-tête UTF-8
   - Le code fourni
5. Exécution avec subprocess.run()
6. Capture de stdout et stderr
7. Retour JSON: {success, output, error}
8. Frontend affiche les résultats
9. Nettoyage du fichier temporaire
```

---

## 📁 Structure des Fichiers

```
OteriaPython/
│
├── 📄 README.md                    # Documentation principale
├── 📄 COMMANDES.md                 # Guide des commandes
├── 📄 AJOUTER_SCRIPTS.md           # Comment ajouter des scripts
├── 📄 ARCHITECTURE.md              # Ce fichier
│
├── 📁 backend/                     # Serveur Python Flask
│   ├── 📄 app.py                  # Point d'entrée, orchestrateur
│   ├── 📄 requirements.txt        # Dépendances Python
│   │
│   ├── 📁 scripts/                # Scripts Python chargés auto
│   │   ├── 📄 README.md
│   │   ├── 🐍 hello_world.py
│   │   ├── 🐍 calculs.py
│   │   ├── 🐍 boucles.py
│   │   ├── 🐍 listes.py
│   │   ├── 🐍 fibonacci.py
│   │   ├── 🐍 dictionnaires.py
│   │   └── 🐍 exemple_complet.py
│   │
│   └── 📁 venv/                   # Environnement virtuel Python
│
├── 📁 frontend/                    # Application React
│   ├── 📄 package.json            # Dépendances npm
│   ├── 📄 vite.config.ts          # Configuration Vite
│   ├── 📄 tsconfig.json           # Configuration TypeScript
│   │
│   ├── 📁 src/
│   │   ├── 📄 main.tsx            # Point d'entrée React
│   │   ├── 📄 App.tsx             # Composant principal
│   │   ├── 📄 App.css             # Styles
│   │   └── 📄 index.css
│   │
│   └── 📁 node_modules/           # Dépendances npm
│
├── 📄 start-backend.ps1            # Script démarrage backend
├── 📄 start-frontend.ps1           # Script démarrage frontend
└── 📄 .gitignore
```

---

## 🔧 Composants Techniques

### Backend (Flask)

| Fichier | Rôle |
|---------|------|
| `app.py` | Serveur Flask, routes API, chargement des scripts |
| `scripts/*.py` | Scripts Python exécutables |
| `requirements.txt` | Flask, flask-cors |
| `venv/` | Environnement virtuel isolé |

**Technologies:**
- Python 3.12
- Flask 3.0.0
- flask-cors 4.0.0

### Frontend (React)

| Fichier | Rôle |
|---------|------|
| `App.tsx` | Composant principal, logique de l'application |
| `App.css` | Styles de l'interface |
| `main.tsx` | Point d'entrée React |

**Technologies:**
- React 19
- TypeScript 5.9
- Vite 7.1

---

## 🔌 API REST

### Endpoints

#### `GET /api/health`
Vérifie que le serveur fonctionne.

**Réponse:**
```json
{
  "status": "ok",
  "message": "Backend Flask est opérationnel"
}
```

#### `GET /api/scripts`
Retourne la liste des scripts disponibles.

**Réponse:**
```json
[
  {
    "id": 1,
    "name": "Hello World",
    "description": "Script simple qui affiche Hello World",
    "category": "Bases",
    "filename": "hello_world.py",
    "code": "# -*- coding: utf-8 -*-\n..."
  },
  ...
]
```

#### `POST /api/execute`
Exécute un script Python.

**Requête:**
```json
{
  "code": "print('Hello World!')"
}
```

**Réponse (succès):**
```json
{
  "success": true,
  "output": "Hello World!\n",
  "error": "",
  "returncode": 0
}
```

**Réponse (erreur):**
```json
{
  "success": false,
  "error": "SyntaxError: invalid syntax"
}
```

---

## 🎨 Interface Utilisateur

### Composants

1. **Header**
   - Titre de l'application
   - Statut de connexion au backend

2. **Sidebar** (Gauche)
   - Liste des scripts disponibles
   - Catégories avec badges
   - Clic pour charger un script

3. **Éditeur** (Centre-haut)
   - Zone de texte pour le code Python
   - Boutons "Effacer" et "Exécuter"

4. **Résultats** (Centre-bas)
   - Affichage de la sortie (stdout)
   - Affichage des erreurs (stderr)

---

## 🔐 Sécurité

### Considérations

⚠️ **Important:** Cette application est pour le développement local uniquement.

**Limitations actuelles:**
- Pas d'authentification
- Exécution de code arbitraire
- Pas de sandbox
- Timeout de 30 secondes par script

**Pour la production:**
- Ajoutez l'authentification
- Utilisez un sandbox (Docker, VM)
- Limitez les imports autorisés
- Ajoutez la validation du code
- Utilisez HTTPS
- Ajoutez des rate limits

---

## 📈 Évolutions Possibles

### Court terme
- [ ] Support des sous-dossiers dans `scripts/`
- [ ] Filtre par catégorie dans l'interface
- [ ] Sauvegarde des scripts personnalisés
- [ ] Export des résultats

### Moyen terme
- [ ] Éditeur de code avec coloration syntaxique (Monaco, CodeMirror)
- [ ] Upload de fichiers pour traitement
- [ ] Graphiques avec matplotlib
- [ ] Historique d'exécution

### Long terme
- [ ] Authentification multi-utilisateurs
- [ ] Base de données pour stocker les scripts
- [ ] Partage de scripts entre utilisateurs
- [ ] Exécution en sandbox sécurisée
- [ ] API publique

---

## 🧪 Tests

### Tester le Backend
```powershell
# Tester l'API health
curl http://localhost:5000/api/health

# Tester l'API scripts
curl http://localhost:5000/api/scripts

# Tester l'exécution
curl -X POST http://localhost:5000/api/execute -H "Content-Type: application/json" -d "{\"code\":\"print('test')\"}"
```

### Tester le Frontend
1. Ouvrir http://localhost:5173
2. Vérifier que le statut backend est "✅ Connecté"
3. Charger un script d'exemple
4. Cliquer sur "Exécuter"
5. Vérifier l'affichage des résultats

---

## 💡 Bonnes Pratiques

### Ajout de scripts
- Toujours inclure l'en-tête UTF-8
- Documenter avec des métadonnées claires
- Tester localement avant d'ajouter
- Utiliser des noms de fichiers descriptifs

### Développement
- Le backend redémarre automatiquement (mode debug)
- Le frontend se recharge automatiquement (hot-reload)
- Consultez les logs dans les terminaux
- Utilisez les DevTools du navigateur

---

**Architecture flexible et extensible ! 🚀**

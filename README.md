# Oteria Python - Exécuteur de Scripts Python

Application web permettant d'exécuter des scripts Python depuis une interface React moderne.

## ✨ Fonctionnalités

- 🚀 **Exécution de scripts Python** en temps réel
- 📁 **Chargement automatique** des scripts depuis le dossier `backend/scripts/`
- 🏷️ **Organisation par catégories** (Bases, Algorithmes, Mathématiques...)
- 🎨 **Interface moderne** avec React + Vite + TypeScript
- 🔄 **Hot-reload** pour le développement
- ✅ **Gestion des erreurs** et affichage des résultats
- 📝 **Éditeur de code** intégré

## Structure du Projet

```
OteriaPython/
├── backend/                    # Serveur Flask (Python)
│   ├── app.py                 # Orchestrateur principal
│   ├── scripts/               # 📁 Scripts Python (chargés automatiquement)
│   │   ├── hello_world.py
│   │   ├── calculs.py
│   │   ├── boucles.py
│   │   ├── listes.py
│   │   ├── fibonacci.py
│   │   ├── dictionnaires.py
│   │   └── README.md
│   ├── requirements.txt
│   └── venv/
├── frontend/                   # Application React + TypeScript
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   ├── package.json
│   └── ...
├── start-backend.ps1          # Script de démarrage backend
├── start-frontend.ps1         # Script de démarrage frontend
├── COMMANDES.md               # 📋 Guide complet des commandes
├── AJOUTER_SCRIPTS.md         # 📝 Comment ajouter des scripts
└── README.md
```

## Installation

### Backend (Python)

1. Créer un environnement virtuel :
```bash
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2. Lancer le serveur Flask :
```bash
python app.py
```

Le backend sera accessible sur http://localhost:5000

### Frontend (React)

1. Installer les dépendances :
```bash
cd frontend
npm install
```

2. Lancer l'application React :
```bash
npm run dev
```

Le frontend sera accessible sur http://localhost:5173

## 🎯 Démarrage Rapide

### 1️⃣ Lancer le Backend
```powershell
cd c:\Users\robin\Code\OteriaPython
.\start-backend.ps1
```

### 2️⃣ Lancer le Frontend (dans un nouveau terminal)
```powershell
cd c:\Users\robin\Code\OteriaPython
.\start-frontend.ps1
```

### 3️⃣ Ouvrir le navigateur
http://localhost:5173

---

## 📝 Ajouter un nouveau script

**C'est ultra simple !** Le système charge automatiquement tous les fichiers `.py` du dossier `backend/scripts/`.

### Créez un fichier dans `backend/scripts/mon_script.py` :

```python
# -*- coding: utf-8 -*-
"""
name: Mon Super Script
description: Description de ce que fait le script
category: Ma Categorie
"""

print("Hello from my script!")
```

### Rechargez la page web → Le script apparaît automatiquement ! 🎉

**📖 Guide complet :** Consultez [`AJOUTER_SCRIPTS.md`](AJOUTER_SCRIPTS.md)

---

## 🏗️ Architecture

- **Frontend** (React + TypeScript) → Port 5173
- **Backend** (Flask + Python) → Port 5000
- **Communication** : API REST (JSON)

```
Frontend ←──(HTTP/JSON)──→ Backend ←──(charge)──→ scripts/*.py
```

### Workflow d'exécution

1. L'utilisateur clique sur un script ou écrit du code
2. Le frontend envoie le code au backend via `/api/execute`
3. Le backend crée un fichier temporaire
4. Python exécute le fichier
5. Les résultats (stdout/stderr) sont renvoyés au frontend
6. Affichage dans l'interface

## API Endpoints

- `GET /api/health` - Vérifier l'état du serveur
- `POST /api/execute` - Exécuter un script Python
- `GET /api/scripts` - Obtenir des scripts d'exemple

# 📋 Guide des Commandes - Oteria Python

## 🚀 Démarrage Rapide

### Option 1: Utiliser les scripts PowerShell (RECOMMANDÉ)

#### Terminal 1 - Backend:
```powershell
cd c:\Users\robin\Code\OteriaPython
.\start-backend.ps1
```

#### Terminal 2 - Frontend:
```powershell
cd c:\Users\robin\Code\OteriaPython
.\start-frontend.ps1
```

### Option 2: Commandes manuelles

#### Terminal 1 - Backend Flask:
```powershell
cd c:\Users\robin\Code\OteriaPython\backend
.\venv\Scripts\Activate.ps1
python app.py
```
**Backend accessible sur:** http://localhost:5000

#### Terminal 2 - Frontend React:
```powershell
cd c:\Users\robin\Code\OteriaPython\frontend
npm run dev
```
**Frontend accessible sur:** http://localhost:5173

---

## ⏹️ Arrêter les Serveurs

Dans chaque terminal où un serveur tourne:
- Appuyez sur **`Ctrl + C`**

---

## 🔄 Redémarrer

1. Arrêtez avec `Ctrl + C`
2. Relancez la commande de démarrage

---

## 🧪 Tester l'API Backend

### Vérifier que le backend fonctionne:
```powershell
curl http://localhost:5000/api/health
```

### Obtenir les scripts d'exemple:
```powershell
curl http://localhost:5000/api/scripts
```

### Exécuter un script Python:
```powershell
curl -X POST http://localhost:5000/api/execute -H "Content-Type: application/json" -d '{"code":"print(\"Hello from API!\")"}'
```

---

## 📦 Gestion des Dépendances

### Backend (Python):
```powershell
cd c:\Users\robin\Code\OteriaPython\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend (React):
```powershell
cd c:\Users\robin\Code\OteriaPython\frontend
npm install
```

---

## 🏗️ Build Production

### Frontend:
```powershell
cd c:\Users\robin\Code\OteriaPython\frontend
npm run build
```

Les fichiers de production seront dans `frontend/dist/`

---

## 🛠️ Commandes Utiles

### Voir les packages Python installés:
```powershell
cd c:\Users\robin\Code\OteriaPython\backend
.\venv\Scripts\Activate.ps1
pip list
```

### Voir les packages npm installés:
```powershell
cd c:\Users\robin\Code\OteriaPython\frontend
npm list
```

### Nettoyer et réinstaller (Frontend):
```powershell
cd c:\Users\robin\Code\OteriaPython\frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

---

## 📝 Structure des URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health
- **Scripts d'exemple**: http://localhost:5000/api/scripts
- **Exécution**: http://localhost:5000/api/execute (POST)

---

## 🔥 Démarrage Complet en 2 Étapes

1. **Ouvrez 2 terminaux dans VS Code** (`Ctrl + Shift + ù`)

2. **Terminal 1 (Backend)**:
   ```powershell
   cd c:\Users\robin\Code\OteriaPython
   .\start-backend.ps1
   ```

3. **Terminal 2 (Frontend)**:
   ```powershell
   cd c:\Users\robin\Code\OteriaPython
   .\start-frontend.ps1
   ```

4. **Ouvrez votre navigateur sur**: http://localhost:5173

---

## ⚡ Raccourcis VS Code

- `Ctrl + Shift + ù` : Nouveau terminal
- `Ctrl + C` : Arrêter le serveur
- `Ctrl + Shift + P` : Palette de commandes
- `F5` : Déboguer

---

## 🐛 Dépannage

### Le backend ne démarre pas:
```powershell
# Vérifier Python
python --version

# Réinstaller les dépendances
cd backend
.\venv\Scripts\Activate.ps1
pip install --force-reinstall -r requirements.txt
```

### Le frontend ne démarre pas:
```powershell
# Vérifier Node.js
node --version
npm --version

# Réinstaller les dépendances
cd frontend
npm install
```

### Port déjà utilisé:
```powershell
# Trouver le processus sur le port 5000 (backend)
netstat -ano | findstr :5000

# Trouver le processus sur le port 5173 (frontend)
netstat -ano | findstr :5173

# Tuer le processus (remplacer PID par le numéro)
taskkill /PID <PID> /F
```

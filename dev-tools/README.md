# Scripts de développement

Scripts pour démarrer et gérer l'environnement de développement.

## Scripts disponibles

### Démarrage complet

**Windows (PowerShell)**
```powershell
.\dev-tools\start-dev.ps1
```

**Linux/Mac**
```bash
./dev-tools/start-dev.sh
```

Lance le backend et le frontend ensemble dans des terminaux séparés.

### Démarrage backend uniquement

**Windows**
```powershell
.\dev-tools\start-backend.ps1
```

**Linux/Mac**
```bash
./dev-tools/start-backend.sh
```

Lance uniquement le serveur Flask (port 5000).

### Démarrage frontend uniquement

**Windows**
```powershell
.\dev-tools\start-frontend.ps1
```

**Linux/Mac**
```bash
./dev-tools/start-frontend.sh
```

Lance uniquement le serveur Vite (port 5173).

## Notes

- Les scripts activent automatiquement les environnements virtuels
- Backend: http://localhost:5000
- Frontend: http://localhost:5173
- Pour Linux/Mac, rendre les scripts exécutables: `chmod +x dev-tools/*.sh`

# Script de demarrage complet (Backend + Frontend)
Write-Host "Initialisation de l'environnement de developpement..." -ForegroundColor Cyan

$rootPath = Get-Location

# --- Backend ---
Write-Host "Configuration du Backend..." -ForegroundColor Yellow
Set-Location "$rootPath\backend"

# 1. Creer l'environnement virtuel s'il n'existe pas
if (-not (Test-Path "venv")) {
    Write-Host "Creation de l'environnement virtuel..."
    python -m venv venv
}

# 2. Activer l'environnement virtuel (pour ce script)
.\venv\Scripts\Activate.ps1

# 3. Installer les dependances demandees
Write-Host "Installation des dependances Python..."
pip install flask flask-cors flask-sqlalchemy flask-login flask-bcrypt python-dotenv

# 4. Initialiser la base de donnees
Write-Host "Initialisation de la base de donnees..."
python init_db.py

# 5. Lancer le serveur Backend dans une nouvelle fenetre
Write-Host "Lancement du serveur Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Backend Flask'; cd '$($rootPath)\backend'; .\venv\Scripts\Activate.ps1; python app.py"

# --- Frontend ---
Write-Host "Configuration du Frontend..." -ForegroundColor Yellow
Set-Location "$rootPath\frontend"

# 1. Installer les dependances Node
Write-Host "Installation des dependances Node..."
npm install

# 2. Lancer le serveur Frontend dans une nouvelle fenetre
Write-Host "Lancement du serveur Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Frontend React'; cd '$($rootPath)\frontend'; npm run dev"

# Retour a la racine
Set-Location $rootPath

Write-Host "Les deux serveurs sont lances dans des fenetres separees !" -ForegroundColor Green

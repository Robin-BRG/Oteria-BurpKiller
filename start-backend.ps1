# Script pour démarrer le backend Flask
Write-Host "🚀 Démarrage du backend Flask..." -ForegroundColor Green
Set-Location backend
.\venv\Scripts\Activate.ps1
Write-Host "✅ Environnement virtuel activé" -ForegroundColor Green
Write-Host "📡 Backend accessible sur http://localhost:5000" -ForegroundColor Cyan
python app.py

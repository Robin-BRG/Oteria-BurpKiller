# Script pour demarrer le backend Flask
Write-Host "Demarrage du backend Flask..." -ForegroundColor Green
Set-Location backend
.\venv\Scripts\Activate.ps1
Write-Host "Environnement virtuel active" -ForegroundColor Green
Write-Host "Backend accessible sur http://localhost:5000" -ForegroundColor Cyan
python app.py

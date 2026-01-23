#!/bin/bash

# Récupérer le chemin absolu du dossier racine du projet
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔵 [Backend] Démarrage..."
cd "$BACKEND_DIR"

# Vérification/Création du venv
if [ ! -d "venv" ]; then
    echo "⚠️  [Backend] Environnement virtuel non trouvé. Création..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 [Backend] Installation des dépendances..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Lancement de Flask
echo "🚀 [Backend] Lancement du serveur Flask sur http://localhost:5000"
python app.py
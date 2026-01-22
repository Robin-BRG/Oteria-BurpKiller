#!/bin/bash
# Script de démarrage du backend Flask pour Linux/Debian

cd "$(dirname "$0")/backend"

# Activer l'environnement virtuel
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
elif [ -f "~/Documents/venv/bin/activate" ]; then
    source ~/Documents/venv/bin/activate
else
    echo "Erreur: Environnement virtuel non trouvé"
    exit 1
fi

# Lancer le serveur Flask
echo "Démarrage du serveur Flask sur http://127.0.0.1:5000"
python app.py

#!/bin/bash
# Script de démarrage du frontend Vite pour Linux/Debian

cd "$(dirname "$0")/frontend"

# Charger nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Vérifier que Node.js est installé
if ! command -v node &> /dev/null; then
    echo "Erreur: Node.js n'est pas installé. Installez-le avec nvm."
    exit 1
fi

# Lancer le serveur Vite
echo "Démarrage du serveur Vite sur http://0.0.0.0:5173"
npm run dev -- --host 0.0.0.0

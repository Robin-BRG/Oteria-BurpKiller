#!/bin/bash

# Script de lancement global pour Linux/Mac

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEV_TOOLS="$PROJECT_ROOT/dev-tools"

# Fonction pour tuer les processus fils à la sortie
cleanup() {
    echo ""
    echo "🔴 Arrêt des services Oteria BurpKiller..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Intercepter Ctrl+C (SIGINT) et SIGTERM
trap cleanup SIGINT SIGTERM

echo "🚀 Lancement de Oteria BurpKiller (Linux/Mac)"
echo "=============================================="

# Rendre les scripts exécutables (au cas où)
chmod +x "$DEV_TOOLS/start-backend.sh"
chmod +x "$DEV_TOOLS/start-frontend.sh"

# Lancer le backend en arrière-plan
"$DEV_TOOLS/start-backend.sh" &

# Attendre un peu que le backend s'initialise
sleep 2

# Lancer le frontend (garde le terminal actif)
"$DEV_TOOLS/start-frontend.sh"
#!/bin/bash
# Script de démarrage complet pour Oteria-BurpKiller sur Linux/Debian

echo "=== Démarrage d'Oteria-BurpKiller ==="
echo ""

# Aller au répertoire du projet
cd "$(dirname "$0")"

# Démarrer le backend en arrière-plan
echo "[1/2] Démarrage du backend Flask..."
./start-backend.sh > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend démarré (PID: $BACKEND_PID)"
sleep 2

# Démarrer le frontend en arrière-plan
echo "[2/2] Démarrage du frontend Vite..."
./start-frontend.sh > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend démarré (PID: $FRONTEND_PID)"

echo ""
echo "=== Application lancée avec succès! ==="
echo ""
echo "Backend:  http://127.0.0.1:5000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Pour arrêter l'application:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""

# Sauvegarder les PIDs
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "PIDs sauvegardés dans .backend.pid et .frontend.pid"

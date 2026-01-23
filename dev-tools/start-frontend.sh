#!/bin/bash

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🟢 [Frontend] Démarrage..."
cd "$FRONTEND_DIR"

# Vérification des node_modules
if [ ! -d "node_modules" ]; then
    echo "⚠️  [Frontend] Dépendances Node non trouvées. Installation..."
    npm install
fi

echo "🚀 [Frontend] Lancement de Vite sur http://localhost:5173"
npm run dev
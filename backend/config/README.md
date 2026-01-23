# Configuration Backend

Fichiers de configuration pour les tests et la couverture de code.

## Fichiers

### pytest.ini

Configuration de pytest pour les tests unitaires.

**Exécuter les tests:**
```bash
cd backend
pytest -c config/pytest.ini
```

**Avec couverture:**
```bash
cd backend
pytest -c config/pytest.ini --cov
```

**Options configurées:**
- Répertoire des tests: `tests/`
- Couverture de code activée par défaut
- Rapport HTML dans `htmlcov/`
- Markers personnalisés: `slow`, `integration`, `unit`, `network`

### .coveragerc

Configuration de coverage.py pour la mesure de couverture de code.

**Exclusions:**
- Environnement virtuel (`venv/`)
- Tests (`tests/`)
- Scripts de scan (`scripts/`)
- Fichiers de configuration (`config/`)
- Utilitaires (`utils/`)

**Rapport HTML:** `backend/htmlcov/index.html`

## Usage

Les fichiers de configuration sont automatiquement utilisés par pytest lorsque vous lancez les tests depuis le répertoire `backend/`.

Pour spécifier explicitement la configuration:
```bash
pytest -c config/pytest.ini --cov-config=config/.coveragerc
```

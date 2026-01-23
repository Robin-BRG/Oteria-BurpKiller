# Tests Unitaires - Oteria BurpKiller

Suite de tests unitaires et d'intégration avec pytest.

## Installation des dépendances de test

```bash
cd backend
pip install -r requirements.txt
```

## Exécution des tests

### Lancer tous les tests

```bash
pytest tests/ -v
```

### Lancer avec la couverture de code

```bash
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
```

### Lancer des tests spécifiques

```bash
# Tester uniquement l'authentification
pytest tests/test_auth.py -v

# Tester uniquement les modèles
pytest tests/test_models.py -v

# Tester uniquement le reporting
pytest tests/test_reports.py -v
```

### Options utiles

```bash
# Afficher les print statements
pytest tests/ -v -s

# Arrêter au premier échec
pytest tests/ -x

# Lancer seulement les tests marqués comme rapides
pytest tests/ -v -m "not slow"
```

## Structure des tests

```
tests/
├── conftest.py              # Fixtures partagées (app, client, users, investigations)
├── test_auth.py             # Tests d'authentification (register, login, logout)
├── test_models.py           # Tests des modèles SQLAlchemy
├── test_investigations.py   # Tests API investigations et membres
├── test_network.py          # Tests module réseau
├── test_reports.py          # Tests génération de rapports
└── README.md                # Ce fichier
```

## Statistiques

- **Total de tests**: 53
- **Tests réussis**: 48 (90%)
- **Tests échoués**: 5 (10%)
- **Couverture de code**: 51%

### Détails de couverture par module

| Module | Couverture | Notes |
|--------|-----------|-------|
| app.py | 98% | Configuration Flask |
| models.py | 94% | Modèles de données |
| auth.py | 79% | Authentification |
| reports.py | 66% | Module reporting |
| investigations.py | 54% | Gestion investigations |
| network.py | 47% | Scan réseau |
| report_generator.py | 44% | Génération rapports |
| enumeration.py | 36% | Énumération technologies |
| recon.py | 29% | Reconnaissance web |
| http_tools.py | 28% | Outils HTTP |
| vulns.py | 27% | Scan vulnérabilités |
| ad.py | 17% | Active Directory |

## Fixtures disponibles

Définies dans `conftest.py`:

- `app`: Application Flask de test
- `client`: Client de test Flask
- `test_user`: Utilisateur de test préconfiguré
- `test_investigation`: Investigation de test
- `authenticated_client`: Client avec utilisateur authentifié

## Exemple d'utilisation

```python
def test_my_feature(authenticated_client, test_investigation):
    """Test de ma nouvelle fonctionnalité"""
    response = authenticated_client.get(
        f'/api/investigations/{test_investigation.id}/my-feature'
    )

    assert response.status_code == 200
    data = response.get_json()
    assert 'result' in data
```

## Rapport de couverture HTML

Après avoir lancé les tests avec `--cov-report=html`, ouvrez:

```
backend/htmlcov/index.html
```

## Bonnes pratiques

1. **Tests isolés**: Chaque test doit être indépendant
2. **Fixtures**: Utiliser les fixtures pour éviter la duplication
3. **Assertions claires**: Messages d'erreur explicites
4. **Coverage**: Viser 80%+ de couverture
5. **Noms descriptifs**: `test_should_return_404_for_nonexistent_investigation`

## TODO - Améliorations futures

- [ ] Corriger les 5 tests échoués d'authentification
- [ ] Augmenter la couverture à 80%+
- [ ] Ajouter tests pour scanners (SQLi, XSS, JS Secrets)
- [ ] Tests de performance (pytest-benchmark)
- [ ] Tests de charge (locust)
- [ ] CI/CD integration (GitHub Actions)

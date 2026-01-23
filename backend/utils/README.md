# Utilitaires Backend

Scripts utilitaires pour la gestion de la base de données et autres tâches administratives.

## Scripts disponibles

### init_db.py

Initialise la base de données SQLite en créant toutes les tables.

**Usage:**
```bash
cd backend
python utils/init_db.py
```

Ou via Python directement:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**Ce que fait le script:**
- Crée le répertoire `instance/` si nécessaire
- Crée toutes les tables définies dans `models.py`
- Affiche un message de confirmation

**Quand l'utiliser:**
- Première installation du projet
- Après suppression de la base de données
- Après modification du schéma (nouvelles tables)

## Notes

Les scripts utilitaires sont des outils d'administration qui ne font pas partie du code de l'application principale.

# 📁 Dossier Scripts

Ce dossier contient tous les scripts Python disponibles dans l'application.

## 📝 Format des scripts

Chaque script doit suivre ce format :

```python
# -*- coding: utf-8 -*-
"""
name: Nom du script
description: Description courte
category: Categorie
"""

# Votre code Python ici
print("Hello!")
```

## 🏷️ Métadonnées requises

- **name**: Nom affiché dans l'interface (obligatoire)
- **description**: Description du script (obligatoire)
- **category**: Catégorie pour organiser les scripts (obligatoire)

## 📂 Catégories disponibles

- `Bases` - Scripts pour débutants
- `Mathematiques` - Calculs et opérations
- `Structures de donnees` - Listes, dictionnaires, sets...
- `Algorithmes` - Algorithmes classiques
- `Fichiers` - Manipulation de fichiers
- `Web` - Requêtes HTTP, APIs
- `Autre` - Autres scripts

## ➕ Ajouter un nouveau script

1. Créez un fichier `.py` dans ce dossier
2. Ajoutez l'en-tête avec les métadonnées
3. Écrivez votre code Python
4. Rechargez le backend - le script apparaîtra automatiquement !

## ⚠️ Important

- Utilisez toujours `# -*- coding: utf-8 -*-` en première ligne
- Les métadonnées doivent être dans un docstring en début de fichier
- Un fichier = un script

# 📝 Comment Ajouter des Scripts

Le système charge **automatiquement** tous les fichiers `.py` du dossier `backend/scripts/`.

## ✨ Création d'un nouveau script

### 1️⃣ Créez un fichier `.py` dans `backend/scripts/`

Exemple : `backend/scripts/mon_script.py`

### 2️⃣ Suivez ce template :

```python
# -*- coding: utf-8 -*-
"""
name: Nom de votre script
description: Description courte et claire
category: Categorie appropriee
"""

# Votre code Python ici
print("Mon super script!")
```

### 3️⃣ Rechargez la page web

Le script apparaît **automatiquement** dans l'interface ! 🎉

---

## 🏷️ Métadonnées (obligatoires)

Les métadonnées sont extraites du **docstring** au début du fichier :

| Champ | Description | Exemple |
|-------|-------------|---------|
| `name` | Nom affiché dans l'interface | `Tri de liste` |
| `description` | Description courte | `Trie une liste de nombres` |
| `category` | Catégorie du script | `Algorithmes` |

---

## 📂 Catégories disponibles

- **Bases** - Scripts pour débutants (hello world, variables, boucles)
- **Mathematiques** - Calculs, opérations mathématiques
- **Structures de donnees** - Listes, dictionnaires, sets, tuples
- **Algorithmes** - Tri, recherche, récursivité
- **Fichiers** - Lecture/écriture de fichiers
- **Web** - Requêtes HTTP, APIs
- **Data Science** - Pandas, numpy, matplotlib
- **Autre** - Scripts divers

💡 **Vous pouvez créer vos propres catégories !**

---

## 📋 Exemples complets

### Exemple 1 : Script simple

```python
# -*- coding: utf-8 -*-
"""
name: Nombres premiers
description: Affiche les nombres premiers jusqu'a 50
category: Algorithmes
"""

def est_premier(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

print("Nombres premiers jusqu'a 50:")
premiers = [n for n in range(2, 51) if est_premier(n)]
print(premiers)
```

### Exemple 2 : Script avec input utilisateur

```python
# -*- coding: utf-8 -*-
"""
name: Calculatrice simple
description: Operations mathematiques de base
category: Mathematiques
"""

# Exemple avec des valeurs pre-definies
a = 15
b = 4

print(f"a = {a}, b = {b}")
print(f"Addition: {a + b}")
print(f"Soustraction: {a - b}")
print(f"Multiplication: {a * b}")
print(f"Division: {a / b:.2f}")
```

### Exemple 3 : Script avec visualisation

```python
# -*- coding: utf-8 -*-
"""
name: Statistiques
description: Calculs statistiques sur une liste
category: Mathematiques
"""

import statistics

donnees = [12, 15, 18, 20, 22, 25, 28, 30]

print("Donnees:", donnees)
print(f"Moyenne: {statistics.mean(donnees):.2f}")
print(f"Mediane: {statistics.median(donnees)}")
print(f"Ecart-type: {statistics.stdev(donnees):.2f}")
print(f"Min: {min(donnees)}, Max: {max(donnees)}")
```

---

## ⚙️ Architecture du système

```
backend/
├── app.py                      # Orchestrateur principal
├── scripts/                    # Dossier des scripts
│   ├── hello_world.py         # ← Chargé automatiquement
│   ├── calculs.py             # ← Chargé automatiquement
│   ├── fibonacci.py           # ← Chargé automatiquement
│   └── mon_nouveau_script.py  # ← Ajoutez le vôtre ici !
└── venv/
```

### Comment ça fonctionne ?

1. **`app.py`** scanne le dossier `scripts/`
2. Il lit chaque fichier `.py`
3. Il extrait les métadonnées du docstring
4. Il charge le code complet
5. Il envoie la liste au frontend via l'API `/api/scripts`

---

## 🔄 Workflow d'ajout

```
1. Créer mon_script.py dans backend/scripts/
2. Ajouter les métadonnées (name, description, category)
3. Écrire le code Python
4. Sauvegarder
5. Le backend détecte automatiquement le nouveau fichier
6. Recharger la page web (F5)
7. Le script apparaît dans la sidebar !
```

---

## ✅ Checklist avant d'ajouter un script

- [ ] Fichier placé dans `backend/scripts/`
- [ ] Extension `.py`
- [ ] Première ligne : `# -*- coding: utf-8 -*-`
- [ ] Docstring avec `name`, `description`, `category`
- [ ] Code testé et fonctionnel
- [ ] Pas d'erreurs de syntaxe

---

## 🐛 Dépannage

### Le script n'apparaît pas ?

1. Vérifiez que le fichier est dans `backend/scripts/`
2. Vérifiez l'extension `.py`
3. Vérifiez le docstring (format correct)
4. Rechargez la page web (F5)
5. Vérifiez les logs du backend

### Erreur d'encodage ?

Ajoutez **toujours** en première ligne :
```python
# -*- coding: utf-8 -*-
```

### Le script ne s'exécute pas ?

- Vérifiez la syntaxe Python
- Regardez les erreurs dans la sortie
- Testez le script en local d'abord

---

## 🚀 Aller plus loin

### Organiser par sous-dossiers (futur)

Actuellement, tous les scripts sont au même niveau. Vous pourriez modifier `app.py` pour supporter :

```
scripts/
├── basics/
│   ├── hello.py
│   └── variables.py
├── algorithms/
│   ├── sorting.py
│   └── searching.py
└── data_science/
    └── pandas_intro.py
```

### Ajouter des paramètres

Modifiez le frontend et le backend pour permettre aux utilisateurs de passer des paramètres aux scripts.

### Sauvegarder les scripts personnalisés

Ajoutez une fonctionnalité pour que les utilisateurs puissent sauvegarder leurs propres scripts.

---

## 💡 Conseils

- **Nommage** : Utilisez des noms de fichiers clairs (`tri_bulles.py` plutôt que `script1.py`)
- **Commentaires** : Commentez votre code pour l'apprentissage
- **Exemples** : Incluez des exemples d'utilisation dans vos scripts
- **Print** : Utilisez `print()` pour afficher les résultats
- **Performance** : Évitez les boucles infinies et les calculs trop longs

---

**Amusez-vous bien ! 🐍✨**

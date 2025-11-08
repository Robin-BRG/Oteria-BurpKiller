# 📦 Installer des Bibliothèques Python

## 🎯 Pour vos scripts d'exécution

Les bibliothèques installées dans l'environnement virtuel du **backend** seront disponibles pour **tous vos scripts**.

### **Méthode 1 : Installation manuelle**

```powershell
# Activer l'environnement virtuel
cd c:\Users\robin\Code\OteriaPython\backend
.\venv\Scripts\Activate.ps1

# Installer les bibliothèques
pip install numpy pandas matplotlib requests

# Mettre à jour requirements.txt
pip freeze > requirements.txt
```

### **Méthode 2 : Via requirements.txt**

1. **Éditez** `backend/requirements.txt` :

```txt
Flask==3.0.0
flask-cors==4.0.0

# Vos bibliothèques
numpy==1.26.0
pandas==2.1.0
matplotlib==3.8.0
requests==2.31.0
```

2. **Installez** :

```powershell
cd c:\Users\robin\Code\OteriaPython\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📚 Bibliothèques Populaires

### **Data Science**
```powershell
pip install numpy pandas matplotlib seaborn scipy
```

### **Web & APIs**
```powershell
pip install requests beautifulsoup4 flask-restful
```

### **Images**
```powershell
pip install pillow opencv-python
```

### **Machine Learning**
```powershell
pip install scikit-learn tensorflow torch
```

### **Utilitaires**
```powershell
pip install python-dateutil pytz colorama tqdm
```

---

## 🧪 Tester une bibliothèque

Une fois installée, créez un script de test :

**`backend/scripts/test_numpy.py`**
```python
# -*- coding: utf-8 -*-
"""
name: Test NumPy
description: Teste si NumPy est installe
category: Tests
"""

try:
    import numpy as np
    print("✅ NumPy est installe!")
    print(f"Version: {np.__version__}")
    
    # Test simple
    arr = np.array([1, 2, 3, 4, 5])
    print(f"Tableau: {arr}")
    print(f"Moyenne: {np.mean(arr)}")
    
except ImportError:
    print("❌ NumPy n'est pas installe")
    print("Pour l'installer: pip install numpy")
```

---

## 📋 Exemple complet avec Pandas

**Installation :**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install pandas
```

**Script :** `backend/scripts/exemple_pandas.py`
```python
# -*- coding: utf-8 -*-
"""
name: Exemple Pandas
description: Manipulation de donnees avec Pandas
category: Data Science
"""

import pandas as pd

# Création d'un DataFrame
data = {
    'nom': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'ville': ['Paris', 'Lyon', 'Marseille', 'Paris']
}

df = pd.DataFrame(data)

print("=== DataFrame ===")
print(df)

print("\n=== Statistiques ===")
print(df.describe())

print("\n=== Filtrage ===")
paris = df[df['ville'] == 'Paris']
print(paris)
```

---

## 📋 Exemple avec Matplotlib

**Installation :**
```powershell
pip install matplotlib
```

**Script :** `backend/scripts/graphique.py`
```python
# -*- coding: utf-8 -*-
"""
name: Graphique Simple
description: Creation d'un graphique avec Matplotlib
category: Visualisation
"""

import matplotlib
matplotlib.use('Agg')  # Backend sans affichage
import matplotlib.pyplot as plt
import io
import base64

# Données
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]

# Créer le graphique
plt.figure(figsize=(8, 6))
plt.plot(x, y, marker='o', linestyle='-', color='blue')
plt.title('Exemple de Graphique')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)

# Sauvegarder en image
plt.savefig('graphique.png')
print("✅ Graphique sauvegarde dans 'graphique.png'")
plt.close()
```

⚠️ **Note :** Pour afficher des graphiques dans le navigateur, il faudra adapter le backend pour envoyer des images.

---

## 🔧 Gestion des versions

### **Lister les packages installés**
```powershell
pip list
```

### **Voir les packages obsolètes**
```powershell
pip list --outdated
```

### **Mettre à jour un package**
```powershell
pip install --upgrade numpy
```

### **Désinstaller un package**
```powershell
pip uninstall numpy
```

---

## 🐛 Dépannage

### **Erreur d'import dans un script ?**

1. Vérifiez que la bibliothèque est installée :
```powershell
pip list | findstr numpy
```

2. Vérifiez que l'environnement virtuel est activé :
```powershell
# Vous devriez voir (venv) au début de la ligne
(venv) PS C:\Users\robin\Code\OteriaPython\backend>
```

3. Réinstallez si nécessaire :
```powershell
pip install --force-reinstall numpy
```

### **Conflit de versions ?**

Créez un environnement virtuel propre :
```powershell
cd backend
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 📊 Exemples de Scripts avec Bibliothèques

### **1. Script avec Requests (API)**

```python
# -*- coding: utf-8 -*-
"""
name: API JSONPlaceholder
description: Recupere des donnees depuis une API
category: Web
"""

import requests

url = "https://jsonplaceholder.typicode.com/users"
response = requests.get(url)

if response.status_code == 200:
    users = response.json()
    print(f"✅ {len(users)} utilisateurs recuperes\n")
    
    for user in users[:3]:  # Affiche les 3 premiers
        print(f"- {user['name']} ({user['email']})")
else:
    print(f"❌ Erreur: {response.status_code}")
```

### **2. Script avec NumPy**

```python
# -*- coding: utf-8 -*-
"""
name: Calculs NumPy
description: Operations matricielles avec NumPy
category: Data Science
"""

import numpy as np

# Matrices
a = np.array([[1, 2], [3, 4]])
b = np.array([[5, 6], [7, 8]])

print("Matrice A:")
print(a)
print("\nMatrice B:")
print(b)

print("\nAddition:")
print(a + b)

print("\nMultiplication matricielle:")
print(np.dot(a, b))

print("\nDeterminant de A:")
print(np.linalg.det(a))
```

---

## ✅ Checklist Installation

- [ ] Environnement virtuel activé (`.\venv\Scripts\Activate.ps1`)
- [ ] Bibliothèque installée (`pip install <package>`)
- [ ] `requirements.txt` mis à jour (`pip freeze > requirements.txt`)
- [ ] Script créé avec `import <package>`
- [ ] Test d'exécution dans l'interface web

---

## 🚀 Aller plus loin

### **Créer un script pour lister les packages disponibles**

**`backend/scripts/packages_installes.py`**
```python
# -*- coding: utf-8 -*-
"""
name: Packages Installes
description: Liste les packages Python disponibles
category: Systeme
"""

import pkg_resources

print("📦 Packages Python installes:\n")

packages = sorted([pkg.key for pkg in pkg_resources.working_set])

for i, package in enumerate(packages, 1):
    version = pkg_resources.get_distribution(package).version
    print(f"{i:2d}. {package:30s} {version}")

print(f"\n✅ Total: {len(packages)} packages")
```

---

**Installez ce dont vous avez besoin et amusez-vous bien ! 🐍📦**

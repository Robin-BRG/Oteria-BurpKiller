# 🐛 Erreurs Courantes et Solutions

## ❌ Erreur d'Encodage Unicode (Windows)

### **Symptôme:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u274c' in position 0
```

### **Cause:**
Sur Windows, le terminal utilise l'encodage `cp1252` qui ne supporte pas les emojis (✅, ❌, 🎉, etc.)

### **Solutions:**

#### **1. Éviter les emojis dans les scripts**
Remplacez les emojis par du texte simple :
```python
# ❌ Provoque l'erreur sur Windows
print("✅ Succès!")

# ✅ Fonctionne partout
print("[OK] Succes!")
```

#### **2. Utiliser des caractères ASCII simples**
```python
print("[OK]  Installé")
print("[--]  Non installé")
print("[!!]  Attention")
print("[**]  Important")
```

#### **3. Configurer l'encodage UTF-8 (avancé)**
Dans votre script :
```python
import sys
import io

# Force UTF-8 pour stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Maintenant les emojis fonctionnent
print("✅ Succès!")
```

---

## 📦 ModuleNotFoundError

### **Symptôme:**
```
ModuleNotFoundError: No module named 'numpy'
```

### **Cause:**
La bibliothèque n'est pas installée dans l'environnement virtuel.

### **Solution:**

```powershell
# 1. Aller dans le backend
cd c:\Users\robin\Code\OteriaPython\backend

# 2. Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# 3. Installer la bibliothèque manquante
pip install numpy

# 4. Vérifier l'installation
pip list | findstr numpy
```

---

## 🔒 ImportError: DLL load failed

### **Symptôme:**
```
ImportError: DLL load failed while importing _ssl
```

### **Cause:**
Bibliothèque système manquante (souvent avec numpy, scipy).

### **Solution:**

1. **Installer Microsoft Visual C++ Redistributable**
   - Téléchargez depuis le site Microsoft
   - Installez la version 2015-2022

2. **Réinstaller la bibliothèque**
   ```powershell
   pip uninstall numpy
   pip install numpy
   ```

---

## 🌐 Erreur de Connexion Backend

### **Symptôme:**
Dans le navigateur : "Backend non accessible"

### **Causes possibles:**

#### **1. Backend non démarré**
**Solution:**
```powershell
cd c:\Users\robin\Code\OteriaPython\backend
.\venv\Scripts\Activate.ps1
python app.py
```

#### **2. Mauvais port**
Vérifiez que Flask tourne sur le port 5000 :
```
* Running on http://127.0.0.1:5000
```

#### **3. CORS bloqué**
Vérifiez que `flask-cors` est installé :
```powershell
pip list | findstr flask-cors
```

---

## 🔥 Erreur Timeout (30 secondes)

### **Symptôme:**
```
Le script a dépassé le délai d'exécution (30 secondes)
```

### **Cause:**
Votre script prend trop de temps (boucle infinie, calcul long).

### **Solutions:**

#### **1. Optimiser le code**
```python
# ❌ Trop lent
for i in range(10000000):
    print(i)

# ✅ Plus rapide
for i in range(100):
    print(i)
```

#### **2. Augmenter le timeout**
Dans `backend/app.py` :
```python
result = subprocess.run(
    [sys.executable, temp_file],
    capture_output=True,
    text=True,
    timeout=60  # ← Changez de 30 à 60 secondes
)
```

---

## 📁 FileNotFoundError

### **Symptôme:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

### **Cause:**
Le fichier n'existe pas ou le chemin est incorrect.

### **Solution:**

```python
# ❌ Chemin relatif (problématique)
with open('data.txt', 'r') as f:
    content = f.read()

# ✅ Vérifier l'existence
import os

if os.path.exists('data.txt'):
    with open('data.txt', 'r') as f:
        content = f.read()
else:
    print("Fichier non trouve!")
```

---

## 🔧 SyntaxError

### **Symptôme:**
```
SyntaxError: invalid syntax
```

### **Causes courantes:**

#### **1. Parenthèse manquante**
```python
# ❌ Erreur
print("Hello"

# ✅ Correct
print("Hello")
```

#### **2. Indentation incorrecte**
```python
# ❌ Erreur
def ma_fonction():
print("test")

# ✅ Correct
def ma_fonction():
    print("test")
```

#### **3. Guillemets non fermés**
```python
# ❌ Erreur
texte = "Hello

# ✅ Correct
texte = "Hello"
```

---

## 🚫 Backend ne redémarre pas automatiquement

### **Symptôme:**
Les modifications dans `app.py` ne sont pas prises en compte.

### **Solutions:**

#### **1. Vérifier le mode debug**
Dans `app.py` :
```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)  # ← debug=True est important
```

#### **2. Redémarrer manuellement**
```powershell
# Dans le terminal backend
Ctrl + C  # Arrêter
python app.py  # Relancer
```

---

## 🎨 Frontend ne se met pas à jour

### **Symptôme:**
Les modifications CSS/React n'apparaissent pas.

### **Solutions:**

#### **1. Vider le cache du navigateur**
- `Ctrl + Shift + R` (Chrome/Edge)
- `Ctrl + F5` (Firefox)

#### **2. Vérifier que Vite tourne**
Dans le terminal frontend, vous devriez voir :
```
VITE v7.2.2  ready in 163 ms
➜  Local:   http://localhost:5173/
```

#### **3. Relancer le frontend**
```powershell
Ctrl + C  # Arrêter
npm run dev  # Relancer
```

---

## 📊 Vérifications de Base

### **Checklist de Dépannage:**

- [ ] Backend tourne sur http://localhost:5000
- [ ] Frontend tourne sur http://localhost:5173
- [ ] Environnement virtuel activé (vous voyez `(venv)`)
- [ ] Pas d'erreurs dans les terminaux
- [ ] Navigateur à jour
- [ ] Cache navigateur vidé

### **Commandes de diagnostic:**

```powershell
# Vérifier Python
python --version

# Vérifier Node
node --version

# Vérifier les packages Python
pip list

# Vérifier les packages npm
npm list --depth=0

# Tester le backend
curl http://localhost:5000/api/health

# Voir les logs en temps réel
# (regardez les terminaux backend et frontend)
```

---

## 🆘 Réinitialisation Complète

Si rien ne fonctionne, réinitialisez tout :

```powershell
# 1. Arrêter tous les serveurs (Ctrl + C)

# 2. Nettoyer le backend
cd c:\Users\robin\Code\OteriaPython\backend
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Nettoyer le frontend
cd ..\frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install

# 4. Relancer
cd ..\backend
.\venv\Scripts\Activate.ps1
python app.py

# 5. Dans un autre terminal
cd c:\Users\robin\Code\OteriaPython\frontend
npm run dev
```

---

## 💡 Bonnes Pratiques pour Éviter les Erreurs

1. **Toujours activer l'environnement virtuel** avant d'installer des packages
2. **Tester les scripts localement** avant de les ajouter
3. **Éviter les emojis** dans les scripts Python sur Windows
4. **Utiliser des chemins absolus** pour les fichiers
5. **Vérifier les logs** dans les terminaux
6. **Commiter régulièrement** avec Git
7. **Documenter** les dépendances spéciales

---

**En cas de doute, consultez les logs et cherchez le message d'erreur ! 🔍**

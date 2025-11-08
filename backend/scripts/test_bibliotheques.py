# -*- coding: utf-8 -*-
"""
name: Test Bibliotheques
description: Verifie quelles bibliotheques sont installees
category: Systeme
"""

import sys
import warnings

# Ignorer les avertissements de dépréciation
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Liste des bibliothèques courantes à tester
bibliotheques = [
    'numpy',
    'pandas', 
    'matplotlib',
    'requests',
    'pillow',
    'scipy',
    'flask',
    'flask_cors'
]

print("=" * 60)
print("VERIFICATION DES BIBLIOTHEQUES INSTALLEES")
print("=" * 60)

installees = []
manquantes = []

for lib in bibliotheques:
    try:
        module = __import__(lib)
        # Essayer d'obtenir la version de différentes manières
        try:
            from importlib.metadata import version as get_version
            version = get_version(lib)
        except:
            version = getattr(module, '__version__', 'version inconnue')
        print(f"[OK] {lib:20s} -> {version}")
        installees.append(lib)
    except ImportError:
        print(f"[--] {lib:20s} -> NON INSTALLE")
        manquantes.append(lib)

print("\n" + "=" * 60)
print(f"Resume: {len(installees)}/{len(bibliotheques)} installees")
print("=" * 60)

if manquantes:
    print("\nPour installer les bibliotheques manquantes:")
    print(f"   pip install {' '.join(manquantes)}")
else:
    print("\nToutes les bibliotheques testees sont installees!")

print(f"\nVersion Python: {sys.version}")

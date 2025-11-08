# -*- coding: utf-8 -*-
"""
name: Dictionnaires
description: Manipulation de dictionnaires Python
category: Structures de donnees
"""

# Creation d'un dictionnaire
personne = {
    "nom": "Dupont",
    "prenom": "Jean",
    "age": 30,
    "ville": "Paris"
}

print("=== Informations ===")
for cle, valeur in personne.items():
    print(f"{cle}: {valeur}")

# Ajout et modification
personne["profession"] = "Developpeur"
personne["age"] = 31

print("\n=== Apres modification ===")
print(personne)

# Verification
print(f"\nLa cle 'nom' existe: {'nom' in personne}")
print(f"Nombre d'elements: {len(personne)}")

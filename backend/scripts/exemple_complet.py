# -*- coding: utf-8 -*-
"""
name: Exemple Complet
description: Demonstration de plusieurs concepts Python
category: Bases
"""

print("=" * 50)
print("EXEMPLE COMPLET - Concepts Python")
print("=" * 50)

# 1. Variables et types
print("\n1. Variables et types:")
nom = "Alice"
age = 25
taille = 1.65
est_etudiant = True
print(f"  Nom: {nom} (type: {type(nom).__name__})")
print(f"  Age: {age} (type: {type(age).__name__})")
print(f"  Taille: {taille}m (type: {type(taille).__name__})")
print(f"  Etudiant: {est_etudiant} (type: {type(est_etudiant).__name__})")

# 2. Listes
print("\n2. Manipulation de listes:")
nombres = [1, 2, 3, 4, 5]
print(f"  Liste originale: {nombres}")
nombres.append(6)
print(f"  Apres append(6): {nombres}")
nombres.remove(3)
print(f"  Apres remove(3): {nombres}")

# 3. Dictionnaires
print("\n3. Dictionnaires:")
personne = {
    "nom": "Bob",
    "age": 30,
    "ville": "Paris"
}
print(f"  Personne: {personne}")
print(f"  Nom: {personne['nom']}")

# 4. Boucles
print("\n4. Boucles:")
print("  Carres des 5 premiers nombres:")
for i in range(1, 6):
    print(f"    {i}^2 = {i**2}")

# 5. Fonctions
print("\n5. Fonctions:")
def calculer_moyenne(liste):
    return sum(liste) / len(liste) if liste else 0

notes = [15, 18, 12, 16, 14]
moyenne = calculer_moyenne(notes)
print(f"  Notes: {notes}")
print(f"  Moyenne: {moyenne:.2f}")

# 6. Conditions
print("\n6. Conditions:")
if moyenne >= 16:
    mention = "Tres bien"
elif moyenne >= 14:
    mention = "Bien"
elif moyenne >= 12:
    mention = "Assez bien"
else:
    mention = "Passable"
print(f"  Mention: {mention}")

print("\n" + "=" * 50)
print("Fin de l'exemple!")
print("=" * 50)

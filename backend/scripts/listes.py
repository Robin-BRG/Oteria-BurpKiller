# -*- coding: utf-8 -*-
"""
name: Listes et comprehension
description: Manipulation de listes Python
category: Structures de donnees
"""

# Creation de liste
nombres = [1, 2, 3, 4, 5]
print("Nombres:", nombres)

# Comprehension de liste
carres = [x**2 for x in nombres]
print("Carres:", carres)

# Filtrage
pairs = [x for x in nombres if x % 2 == 0]
print("Nombres pairs:", pairs)

# Operations
print("Somme:", sum(nombres))
print("Maximum:", max(nombres))
print("Minimum:", min(nombres))

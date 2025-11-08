# -*- coding: utf-8 -*-
"""
name: Boucles
description: Exemple avec boucle for
category: Bases
"""

print("=== Boucle simple ===")
for i in range(1, 6):
    print(f"Iteration {i}")

print("\n=== Boucle avec enumerate ===")
fruits = ["pomme", "banane", "orange"]
for index, fruit in enumerate(fruits, 1):
    print(f"{index}. {fruit}")

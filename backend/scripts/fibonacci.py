# -*- coding: utf-8 -*-
"""
name: Suite de Fibonacci
description: Calcul de la suite de Fibonacci
category: Algorithmes
"""

def fibonacci(n):
    """Calcule le n-ieme nombre de Fibonacci"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print("Suite de Fibonacci:")
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")

# Version optimisee avec cache
print("\n=== Version optimisee ===")
def fibonacci_cache(n, cache={}):
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    cache[n] = fibonacci_cache(n-1, cache) + fibonacci_cache(n-2, cache)
    return cache[n]

for i in range(15):
    print(f"F({i}) = {fibonacci_cache(i)}")

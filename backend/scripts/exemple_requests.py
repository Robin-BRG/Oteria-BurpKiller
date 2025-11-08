# -*- coding: utf-8 -*-
"""
name: Exemple API Web
description: Recupere des donnees depuis une API (necessite requests)
category: Web
"""

# Vérifier si requests est installé
try:
    import requests
except ImportError:
    print("[ERREUR] La bibliotheque 'requests' n'est pas installee")
    print("Pour l'installer: pip install requests")
    exit(1)

print("=== Recuperation de donnees depuis une API ===\n")

# API publique de test
url = "https://jsonplaceholder.typicode.com/posts/1"

try:
    print(f"[API] Appel de l'API: {url}")
    response = requests.get(url, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n[OK] Donnees recuperees avec succes!\n")
        print(f"User ID: {data['userId']}")
        print(f"Post ID: {data['id']}")
        print(f"Titre: {data['title']}")
        print(f"\nContenu:\n{data['body']}")
    else:
        print(f"[ERREUR] Erreur HTTP: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("[ERREUR] Timeout: L'API ne repond pas")
except requests.exceptions.RequestException as e:
    print(f"[ERREUR] Erreur de connexion: {e}")

# Scripts Python pour la Cybersecurite

Ce dossier contient les scripts Python qui utilisent des outils de cybersecurite.

## Structure

Chaque script doit avoir un docstring au debut avec les metadonnees suivantes :

```python
"""
name: Nom du script
description: Description courte
category: Categorie (Recon, Enum, Exploit, etc.)
"""
```

## Scripts disponibles

### Reconnaissance
- `http_scanner.py` : Scanner HTTP pour la decouverte de paths

### Enumeration
- `tech_detector.py` : Detection de technologies et analyse des headers HTTP

### Exploitation
- `sqli_scanner.py` : Detection automatique de SQL Injection (error-based, boolean-based)
- `xss_scanner.py` : Detection de Cross-Site Scripting (reflected XSS)
- `js_secret_scanner.py` : Analyse JavaScript pour detecter les secrets (API keys, tokens, JWT, endpoints caches)

## Usage

Les scripts sont automatiquement charges par l'API Flask et peuvent etre executes via les endpoints appropries.

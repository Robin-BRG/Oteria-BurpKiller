# Scripts de Cybersécurité - Oteria BurpKiller

Ce dossier contient les scripts Python organisés par catégorie de pentest.

## Structure

```
scripts/
├── recon/          # Reconnaissance
├── enum/           # Enumération
└── exploit/        # Exploitation
```

## Scripts disponibles

### Reconnaissance (recon/)

**`http_scanner.py`** - Scanner de paths HTTP
- Découverte de répertoires et fichiers web
- Modes : stealth, normal, aggressive
- Wordlists : COMMON_PATHS (25), AGGRESSIVE_PATHS (100+)
- Métadonnées :
  ```python
  name: HTTP Scanner
  description: Scanner de paths et directories HTTP
  category: Recon
  ```

### Enumération (enum/)

**`tech_detector.py`** - Détection de technologies
- Analyse des headers HTTP de sécurité
- Détection de frameworks, CMS, serveurs
- Évaluation du niveau de sécurité
- Métadonnées :
  ```python
  name: Technology Detector
  description: Detection de technologies et analyse headers HTTP
  category: Enum
  ```

### Exploitation (exploit/)

**`sqli_scanner.py`** - Scanner SQL Injection
- Détection error-based et boolean-based
- Payloads pour MySQL, PostgreSQL, MSSQL, Oracle
- Tests sur paramètres GET et POST
- Métadonnées :
  ```python
  name: SQLi Scanner
  description: Detection automatique de SQL Injection
  category: Exploit
  ```

**`xss_scanner.py`** - Scanner XSS
- Détection de reflected XSS
- Payloads variés (balises script, events, encodage)
- Tests sur paramètres GET et POST
- Métadonnées :
  ```python
  name: XSS Scanner
  description: Detection de Cross-Site Scripting
  category: Exploit
  ```

**`js_secret_scanner.py`** - Scanner de secrets JavaScript
- Détection de clés API exposées
- Patterns : Google API, AWS, Stripe, GitHub tokens, JWT
- Extraction d'endpoints API cachés
- Métadonnées :
  ```python
  name: JS Secret Scanner
  description: Analyse JavaScript pour detecter secrets et API keys
  category: Exploit
  ```

## Convention de nommage

Chaque script doit avoir un docstring au début avec les métadonnées suivantes :

```python
"""
name: Nom du script
description: Description courte
category: Recon | Enum | Exploit
"""
```

## Usage

Les scripts sont automatiquement chargés par l'API Flask via les blueprints :
- `recon.py` → utilise `scripts/recon/`
- `enumeration.py` → utilise `scripts/enum/`
- `vulns.py` → utilise `scripts/exploit/`

Les chemins d'import sont configurés dynamiquement avec `sys.path.insert()`.

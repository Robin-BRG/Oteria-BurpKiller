# Système de Logging Structuré

Le projet utilise un système de logging structuré basé sur le module `logging` de Python.

## Configuration

Le logging est configuré dans [logger_config.py](logger_config.py).

### Niveaux de log

- **DEBUG**: Informations détaillées de débogage
- **INFO**: Informations générales sur le fonctionnement
- **WARNING**: Avertissements (ex: tentatives de connexion échouées)
- **ERROR**: Erreurs (ex: exceptions capturées)
- **CRITICAL**: Erreurs critiques

### Fichiers de logs

Les logs sont stockés dans le répertoire `backend/logs/`:

| Fichier | Description | Contenu |
|---------|-------------|---------|
| `oteria.log` | Log général | Tous les logs (DEBUG et plus) |
| `oteria_errors.log` | Erreurs uniquement | Logs ERROR et CRITICAL |
| `oteria_scans.log` | Activité scans | Logs des scans (recon, network, AD, vulns) |

### Rotation des logs

- Taille maximale par fichier: 10 MB
- Nombre de backups: 5 (général), 10 (scans)
- Format: `oteria.log`, `oteria.log.1`, `oteria.log.2`, etc.

## Utilisation dans le code

### Importer le logger

```python
from logger_config import get_logger

logger = get_logger('module_name')
```

### Logs simples

```python
logger.debug('Message de debug')
logger.info('Opération réussie')
logger.warning('Attention: ressource limitée')
logger.error('Erreur lors du traitement')
logger.critical('Erreur critique système')
```

### Logger une exception

```python
try:
    # Code qui peut échouer
    risky_operation()
except Exception as e:
    logger.exception(f'Erreur dans risky_operation: {str(e)}')
```

### Logger une activité de scan

```python
from logger_config import log_scan_activity

log_scan_activity(
    logger,
    scan_type='network',
    investigation_id=123,
    target='192.168.1.1',
    status='completed',
    ports_found=5,
    duration=12.5
)
```

### Logger un événement de sécurité

```python
from logger_config import log_security_event

log_security_event(
    logger,
    event_type='login_failure',
    user_id='unknown',
    details=f'Failed attempt for email: {email}',
    severity='warning'
)
```

## Exemples par module

### Module d'authentification

```python
# auth.py
from logger_config import get_logger, log_security_event

logger = get_logger('auth')

# Lors d'une inscription
logger.info(f'New user registered: {username}')
log_security_event(logger, 'user_registration', user.id, f'Username: {username}')

# Lors d'un login réussi
logger.info(f'User logged in: {user.username}')
log_security_event(logger, 'login_success', user.id, f'Username: {user.username}')

# Lors d'un login échoué
logger.warning(f'Failed login attempt for email: {email}')
log_security_event(logger, 'login_failure', 'unknown', f'Email: {email}', severity='warning')
```

### Module de scan réseau

```python
# network.py
from logger_config import get_logger, log_scan_activity

logger = get_logger('network')

# Début du scan
logger.info(f'Starting network scan on {target}')
log_scan_activity(logger, 'network', inv_id, target, 'started')

# Scan terminé
logger.info(f'Network scan completed: {len(results)} ports found')
log_scan_activity(logger, 'network', inv_id, target, 'completed', ports_found=len(results))

# Scan échoué
logger.error(f'Network scan failed: {str(error)}')
log_scan_activity(logger, 'network', inv_id, target, 'failed', error=str(error))
```

## Middleware Flask

Le fichier `app.py` inclut un middleware qui log automatiquement:

- **Toutes les requêtes HTTP** entrantes (méthode, path, user, IP)
- **Toutes les réponses HTTP** (status code, durée, user)

Exemple de log:

```
2026-01-22 22:15:30 - oteria.app - INFO - Request: GET /api/investigations/1 - User: 5 - IP: 127.0.0.1
2026-01-22 22:15:30 - oteria.app - INFO - Response: GET /api/investigations/1 - Status: 200 - Duration: 45.23ms - User: 5
```

## Format des logs

Format complet:

```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - [filename:line] - message
```

Exemple:

```
2026-01-22 22:15:30 - oteria.auth - INFO - [auth.py:95] - User logged in: testuser (ID: 5)
```

## Console vs Fichiers

- **Console**: Logs INFO et supérieurs (format simplifié)
- **Fichiers**: Tous les logs DEBUG et supérieurs (format complet)

## Désactiver les logs en production

Pour réduire la verbosité en production:

```python
# logger_config.py
logger = setup_logging('oteria', logging.WARNING)  # Au lieu de DEBUG
```

Ou via variable d'environnement:

```python
import os

log_level = logging.DEBUG if os.getenv('ENV') == 'development' else logging.WARNING
logger = setup_logging('oteria', log_level)
```

## Monitoring des logs

### Rechercher des erreurs

```bash
# Afficher les erreurs récentes
tail -f backend/logs/oteria_errors.log

# Compter les erreurs d'une journée
grep "2026-01-22" backend/logs/oteria_errors.log | wc -l

# Chercher des tentatives de connexion échouées
grep "login_failure" backend/logs/oteria.log
```

### Analyser les scans

```bash
# Voir l'activité des scans
tail -f backend/logs/oteria_scans.log

# Compter les scans complétés
grep "status=completed" backend/logs/oteria_scans.log | wc -l
```

## Intégration avec outils de monitoring

Le format structuré permet l'intégration avec:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Graylog**
- **Splunk**
- **DataDog**

Exemple de parsing pour ELK:

```
%{TIMESTAMP_ISO8601:timestamp} - %{DATA:logger} - %{LOGLEVEL:level} - \[%{DATA:file}:%{NUMBER:line}\] - %{GREEDYDATA:message}
```

## Bonnes pratiques

1. **Utiliser le bon niveau**: DEBUG pour dev, INFO pour production
2. **Messages clairs**: Inclure contexte (user_id, investigation_id, etc.)
3. **Pas de données sensibles**: Jamais de mots de passe, tokens, etc.
4. **Logger les exceptions**: Utiliser `logger.exception()` dans les `except`
5. **Rotation automatique**: Les fichiers de logs se gèrent automatiquement

## Performance

Le logging structuré a un impact minimal sur les performances:

- Rotation asynchrone des fichiers
- Buffering automatique
- Pas de blocage I/O pour l'application

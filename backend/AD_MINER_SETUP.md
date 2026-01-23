# Configuration AD-Miner avec Neo4j

Ce document explique comment configurer et utiliser AD-Miner avec l'application Oteria-BurpKiller pour une analyse approfondie d'Active Directory.

## Prérequis

### 1. Neo4j Database

AD-Miner nécessite Neo4j pour stocker et analyser les données BloodHound.

**Installation Docker (Recommandé)**:
```bash
docker run -d \
  --name neo4j-bloodhound \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/bloodhound \
  neo4j:latest
```

**Installation manuelle**:
1. Télécharger Neo4j Community Edition: https://neo4j.com/download/
2. Installer et démarrer Neo4j
3. Changer le mot de passe par défaut (neo4j/neo4j) vers `bloodhound`
4. S'assurer que les ports 7474 (HTTP) et 7687 (Bolt) sont ouverts

### 2. Librairie Python Neo4j

```bash
pip install neo4j
```

### 3. AD-Miner

**Installation**:
```bash
# Depuis PyPI
pip install ad-miner

# Ou depuis GitHub
git clone https://github.com/Mazars-Tech/AD_Miner.git
cd AD_Miner
pip install -r requirements.txt
pip install .
```

**Vérifier l'installation**:
```bash
AD-Miner --version
```

## Modes d'analyse disponibles

L'application offre deux modes d'analyse BloodHound:

### 1. **Parser Natif (par défaut)**
- Analyse rapide sans dépendances externes
- Parse directement les fichiers JSON BloodHound
- Détecte les vulnérabilités courantes (Kerberoasting, AS-REP Roasting, ACL abuse, etc.)
- Pas besoin de Neo4j ou AD-Miner

### 2. **Neo4j + AD-Miner (complet)**
- Analyse approfondie avec visualisation des graphes
- Utilise Neo4j pour stocker les relations AD
- Exécute AD-Miner pour générer un rapport HTML complet
- Détecte des chemins d'attaque complexes et des relations cachées

## Workflow d'utilisation

### Option A: Parser Natif (Simple)

1. Uploader des fichiers BloodHound (JSON ou ZIP)
2. L'analyse démarre automatiquement
3. Voir les résultats dans l'onglet "BloodHound"

### Option B: Neo4j + AD-Miner (Complet)

1. **S'assurer que Neo4j est démarré**
   ```bash
   # Vérifier avec Docker
   docker ps | grep neo4j-bloodhound

   # Ou vérifier localement
   curl http://localhost:7474
   ```

2. **Uploader les fichiers BloodHound**
   - Aller dans l'onglet "BloodHound"
   - Cliquer sur "Upload BloodHound"
   - Sélectionner les fichiers JSON ou ZIP
   - Choisir "Neo4j + AD-Miner" comme méthode d'analyse

3. **Configurer Neo4j** (si différent des valeurs par défaut)
   - Host: `localhost`
   - Port: `7687`
   - Username: `neo4j`
   - Password: `bloodhound`

4. **Import dans Neo4j**
   - L'application importe automatiquement les données dans Neo4j
   - Les relations entre objets AD sont créées
   - Status visible dans l'interface

5. **Exécution d'AD-Miner**
   - Une fois l'import Neo4j terminé, AD-Miner s'exécute automatiquement
   - Génère un rapport HTML complet
   - Analyse approfondie des chemins d'attaque

6. **Consulter les résultats**
   - Voir le rapport HTML d'AD-Miner directement dans l'interface
   - Filtrer les findings par sévérité et catégorie
   - Explorer les chemins d'attaque visuellement

## Configuration avancée

### Variables d'environnement

```bash
# Configuration Neo4j personnalisée
export NEO4J_HOST=localhost
export NEO4J_PORT=7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=bloodhound

# Dossier de sortie AD-Miner
export ADMINER_REPORTS_FOLDER=/path/to/reports
```

### API Endpoints

```python
# Tester la connexion Neo4j
POST /api/neo4j/test
{
  "host": "localhost",
  "port": 7687,
  "username": "neo4j",
  "password": "bloodhound"
}

# Importer dans Neo4j
POST /api/bloodhound/<analysis_id>/neo4j/import
{
  "host": "localhost",
  "port": 7687,
  "username": "neo4j",
  "password": "bloodhound"
}

# Exécuter AD-Miner
POST /api/bloodhound/<analysis_id>/adminer/run
{
  "host": "localhost",
  "port": 7687,
  "username": "neo4j",
  "password": "bloodhound"
}

# Récupérer le rapport AD-Miner
GET /api/bloodhound/<analysis_id>/adminer/report
```

## Dépannage

### Neo4j ne démarre pas
```bash
# Vérifier les logs Docker
docker logs neo4j-bloodhound

# Redémarrer le conteneur
docker restart neo4j-bloodhound
```

### Erreur "neo4j library not installed"
```bash
pip install neo4j
```

### Erreur "AD-Miner not found"
```bash
# Vérifier l'installation
which AD-Miner

# Réinstaller
pip install --upgrade ad-miner
```

### Timeout Neo4j
- Augmenter le timeout dans le code
- Vérifier que le port 7687 est accessible
- Vérifier les credentials

### Rapport AD-Miner vide
- S'assurer que des données ont bien été importées dans Neo4j
- Vérifier les logs d'exécution d'AD-Miner
- Vérifier que le domaine contient des objets AD

## Performances

**Parser Natif**:
- Rapide (quelques secondes)
- Faible utilisation mémoire
- Bon pour l'analyse rapide

**Neo4j + AD-Miner**:
- Plus lent (1-5 minutes selon la taille du domaine)
- Utilisation mémoire élevée
- Meilleur pour l'analyse approfondie et la détection de chemins complexes

## Références

- **BloodHound**: https://github.com/BloodHoundAD/BloodHound
- **AD-Miner**: https://github.com/Mazars-Tech/AD_Miner
- **Neo4j**: https://neo4j.com/
- **SharpHound**: https://github.com/BloodHoundAD/SharpHound
- **bloodhound-python**: https://github.com/fox-it/BloodHound.py

## Support

Pour les problèmes spécifiques à AD-Miner, consulter la documentation officielle:
https://github.com/Mazars-Tech/AD_Miner/blob/main/README.md

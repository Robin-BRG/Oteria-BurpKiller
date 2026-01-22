# Oteria BurpKiller

Framework de pentest modulaire en Python integrant les domaines Web, Reseau et Active Directory. Developpe dans le cadre du cours "Python pour la Cyber" - M1 2025-2026.

## Table des matieres

1. [Presentation](#presentation)
2. [Fonctionnalites](#fonctionnalites)
3. [Architecture technique](#architecture-technique)
4. [Installation](#installation)
5. [Utilisation](#utilisation)
6. [API Reference](#api-reference)
7. [Structure du projet](#structure-du-projet)
8. [Securite et avertissements](#securite-et-avertissements)

---

## Presentation

BurpKiller est une application web collaborative de tests de securite. Elle centralise les outils de pentest et automatise les taches recurrentes lors d'un test d'intrusion.

### Domaines couverts

| Domaine | Modules |
|---------|---------|
| Web | Reconnaissance HTTP, Enumeration technologies, SQLi, XSS, JS Secrets, Request Builder |
| Reseau | Scan de ports TCP, Ping sweep, Banner grabbing, Detection de services |
| Active Directory | Detection de DC, Enumeration LDAP, Verification SMB/Kerberos |

### Stack technique

**Backend**
- Python 3.8+
- Flask 3.0.0
- SQLAlchemy ORM
- Flask-Login / Flask-Bcrypt
- BeautifulSoup4, Requests

**Frontend**
- React 19 + TypeScript
- Vite 7.x
- React Router v7
- React Flow (visualisation graphe)

**Base de donnees**
- SQLite (developpement)
- PostgreSQL (production)

---

## Fonctionnalites

### Module Web

#### Reconnaissance HTTP
- Scanner de paths avec wordlists configurables
- Modes de scan : stealth (1 req/s), normal (5 req/s), aggressive (20 req/s)
- Visualisation en graphe hierarchique ou liste
- Export PNG du graphe
- Progression en temps reel

#### Enumeration
- Detection automatique des technologies (serveur, framework, CMS, frontend)
- Analyse des headers HTTP de securite (HSTS, CSP, X-Frame-Options, etc.)
- Evaluation du niveau de securite par header

#### Exploitation
- Scanner SQL Injection (error-based, boolean-based)
- Scanner XSS (reflected)
- Detection de secrets JavaScript :
  - Google API Keys
  - AWS Access/Secret Keys
  - Stripe Keys
  - GitHub Tokens
  - JWT Tokens
  - Endpoints API caches
- Request Builder HTTP (equivalent Burp Repeater)
- Historique des requetes avec replay

### Module Reseau

#### Scan de ports
- Modes : quick (25 ports), full (100+ ports), all (1-65535)
- Detection automatique des services
- Banner grabbing
- Protocole TCP

#### Decouverte d'hotes
- Ping sweep sur plages CIDR
- Resolution DNS inverse
- Detection d'hotes actifs

### Module Active Directory

#### Detection de DC
- Identification des controleurs de domaine
- Score de confiance base sur les ports ouverts
- Indicateurs : Kerberos, LDAP, Global Catalog, etc.

#### Enumeration
- Verification LDAP anonyme
- Detection de sessions NULL SMB
- Verification du service Kerberos
- Ports AD standards (88, 389, 636, 445, 3268, 9389)

### Collaboration

- Systeme d'authentification (register/login)
- Enquetes collaboratives multi-utilisateurs
- Gestion des permissions (viewer, editor, admin)
- Partage de fichiers entre membres
- Historique des actions

---

## Architecture technique

### Schema general

```
+----------------+          +----------------+          +----------------+
|    Frontend    |  <--->   |    Backend     |  <--->   |   Database     |
|  React + TS    |   API    |     Flask      |   ORM    |    SQLite      |
|   Port 5173    |   REST   |   Port 5000    |          |                |
+----------------+          +----------------+          +----------------+
```

### Modele de donnees

```
User
  |-- owned_investigations (1:N)
  |-- memberships (N:M via InvestigationMember)

Investigation
  |-- members (1:N)
  |-- files (1:N)
  |-- scans (1:N) -> ReconScan -> ReconResult
  |-- enum_scans (1:N) -> EnumScan -> EnumResult
  |-- network_scans (1:N) -> NetworkScan -> NetworkResult
  |-- ad_scans (1:N) -> ADScan -> ADResult
  |-- vuln_scans (1:N) -> VulnerabilityScan -> Vulnerability
  |-- http_requests (1:N)
  |-- js_secrets (1:N)
```

---

## Installation

### Prerequis

- Python 3.8 ou superieur
- Node.js 16 ou superieur
- Git

### Installation du backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

Initialiser la base de donnees :

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

Lancer le serveur :

```bash
python app.py
```

Le backend est accessible sur http://localhost:5000

### Installation du frontend

```bash
cd frontend
npm install
npm run dev
```

Le frontend est accessible sur http://localhost:5173

### Scripts de demarrage automatique

**Windows (PowerShell)**
```powershell
.\start-dev.ps1
```

**Linux/Mac**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

---

## Utilisation

### 1. Authentification

1. Acceder a http://localhost:5173
2. Creer un compte (Register)
3. Se connecter (Login)

### 2. Creer une investigation

1. Cliquer sur "Nouvelle enquete"
2. Renseigner :
   - Nom de l'enquete
   - URL cible (ex: https://example.com)
   - Description (optionnel)
   - Options : publique, collaborative

### 3. Modules disponibles

#### Onglet Reconnaissance
- Configurer le mode de scan et la wordlist
- Lancer le scan
- Visualiser les resultats en graphe ou liste
- Cliquer sur un noeud pour voir les details

#### Onglet Enumeration
- Lancer l'analyse des technologies
- Consulter les headers de securite
- Voir les technologies detectees

#### Onglet Network
- Entrer l'IP ou le hostname cible
- Choisir le type de scan (quick/full/all) ou ping sweep
- Lancer le scan
- Voir les ports ouverts et services detectes

#### Onglet Active Directory
- Entrer l'IP du controleur de domaine suppose
- Utiliser "Detecter DC" pour verifier
- Lancer un scan basic ou full
- Consulter les resultats d'enumeration

#### Onglet Exploitation
- Scanner SQLi : detecte les injections SQL
- Scanner XSS : detecte les failles XSS reflected
- Scanner JS : detecte les secrets exposes dans le JavaScript
- Request Builder : envoyer des requetes HTTP manuelles
- Historique HTTP : consulter et rejouer les requetes

#### Onglet Rapport
- Aperçu des statistiques de l'investigation
- Génération de rapports HTML professionnels
- Téléchargement PDF (nécessite GTK+ sur Windows, ou utiliser Imprimer > PDF du navigateur)
- Résumé exécutif avec compteurs de vulnérabilités
- Tableaux détaillés de tous les résultats de scans

---

## API Reference

### Authentification

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/register | Creer un compte |
| POST | /api/login | Se connecter |
| POST | /api/logout | Se deconnecter |
| GET | /api/check-auth | Verifier l'authentification |
| GET | /api/me | Obtenir l'utilisateur courant |

### Investigations

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/investigations | Liste des investigations |
| POST | /api/investigations | Creer une investigation |
| GET | /api/investigations/:id | Details d'une investigation |
| PUT | /api/investigations/:id | Modifier une investigation |
| DELETE | /api/investigations/:id | Supprimer une investigation |
| POST | /api/investigations/:id/members | Ajouter un membre |
| GET | /api/investigations/:id/members | Lister les membres |
| POST | /api/investigations/:id/files | Uploader un fichier |
| GET | /api/investigations/:id/files | Lister les fichiers |

### Reconnaissance Web

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/investigations/:id/scans | Lancer un scan |
| GET | /api/investigations/:id/scans | Liste des scans |
| GET | /api/scans/:id | Statut d'un scan |
| GET | /api/scans/:id/results | Resultats d'un scan |

### Enumeration

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/investigations/:id/enum | Lancer scan enumeration |
| GET | /api/investigations/:id/enum | Liste des scans enum |
| GET | /api/enum/:id/results | Resultats enumeration |

### Network

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/investigations/:id/network-scans | Lancer scan reseau |
| GET | /api/investigations/:id/network-scans | Liste des scans reseau |
| GET | /api/network-scans/:id | Statut d'un scan |
| GET | /api/network-scans/:id/results | Resultats scan reseau |

### Active Directory

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/investigations/:id/ad-scans | Lancer scan AD |
| GET | /api/investigations/:id/ad-scans | Liste des scans AD |
| GET | /api/ad-scans/:id | Statut d'un scan AD |
| GET | /api/ad-scans/:id/results | Resultats scan AD |
| POST | /api/investigations/:id/detect-dc | Detecter si cible est un DC |

### Exploitation

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/investigations/:id/vuln-scan | Lancer scan vulnerabilites |
| GET | /api/investigations/:id/vuln-scans | Liste des scans vulns |
| GET | /api/vuln-scans/:id/results | Resultats vulnerabilites |
| POST | /api/investigations/:id/js-scan | Lancer scan JavaScript |
| GET | /api/investigations/:id/js-secrets | Secrets JavaScript trouves |

### HTTP Tools

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /api/investigations/:id/http-requests | Envoyer requete HTTP |
| GET | /api/investigations/:id/http-requests | Historique requetes |
| GET | /api/http-requests/:id | Details requete |
| DELETE | /api/http-requests/:id | Supprimer requete |

### Reporting

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | /api/investigations/:id/report/html | Generer rapport HTML |
| GET | /api/investigations/:id/report/pdf | Telecharger rapport PDF |
| GET | /api/investigations/:id/report/preview | Apercu donnees rapport |

---

## Structure du projet

```
Oteria-BurpKiller/
|
|-- backend/
|   |-- app.py                    # Point d'entree Flask
|   |-- models.py                 # Modeles SQLAlchemy (14 tables)
|   |-- auth.py                   # Blueprint authentification
|   |-- investigations.py         # Blueprint investigations
|   |-- recon.py                  # Blueprint reconnaissance web
|   |-- enumeration.py            # Blueprint enumeration
|   |-- network.py                # Blueprint scan reseau
|   |-- ad.py                     # Blueprint Active Directory
|   |-- vulns.py                  # Blueprint vulnerabilites
|   |-- http_tools.py             # Blueprint HTTP tools
|   |-- reports.py                # Blueprint reporting
|   |-- report_generator.py       # Generateur de rapports HTML/PDF
|   |-- requirements.txt          # Dependances Python
|   |
|   |-- scripts/
|   |   |-- http_scanner.py       # Scanner de paths HTTP
|   |   |-- tech_detector.py      # Detection de technologies
|   |   |-- sqli_scanner.py       # Scanner SQL Injection
|   |   |-- xss_scanner.py        # Scanner XSS
|   |   |-- js_secret_scanner.py  # Scanner secrets JavaScript
|   |
|   |-- instance/
|       |-- app.db                # Base de donnees SQLite
|
|-- frontend/
|   |-- src/
|   |   |-- App.tsx               # Routeur principal
|   |   |
|   |   |-- pages/
|   |   |   |-- Home.tsx          # Page d'accueil
|   |   |   |-- Login.tsx         # Page connexion
|   |   |   |-- Register.tsx      # Page inscription
|   |   |   |-- Investigation.tsx # Page investigation (onglets)
|   |   |   |-- InvestigationsList.tsx
|   |   |
|   |   |-- components/
|   |   |   |-- ReconGraph.tsx    # Visualisation graphe
|   |   |   |-- ReconList.tsx     # Liste resultats recon
|   |   |   |-- EnumDisplay.tsx   # Affichage enumeration
|   |   |   |-- NetworkDisplay.tsx # Affichage scan reseau
|   |   |   |-- ADDisplay.tsx     # Affichage scan AD
|   |   |   |-- VulnDisplay.tsx   # Affichage vulnerabilites
|   |   |   |-- RequestBuilder.tsx # Builder HTTP
|   |   |   |-- HttpHistory.tsx   # Historique requetes
|   |   |   |-- ReportGenerator.tsx # Generateur de rapports
|   |   |
|   |   |-- context/
|   |       |-- AuthContext.tsx   # Context authentification
|   |
|   |-- package.json
|   |-- vite.config.ts
|
|-- start-dev.ps1                 # Script demarrage Windows
|-- start-dev.sh                  # Script demarrage Linux/Mac
|-- README.md                     # Documentation
```

---

## Securite et avertissements

### Usage legal

Cet outil est destine a un usage educatif et professionnel autorise uniquement.

- Ne testez JAMAIS des applications sans autorisation explicite ecrite
- Respectez les lois et reglementations en vigueur (RGPD, LCEN, etc.)
- Utilisez uniquement sur vos propres applications ou avec permission du proprietaire
- Les scans peuvent etre detectes par les WAF et systemes de detection d'intrusion

### Limitations

Ce projet est developpe dans un cadre pedagogique. Les scanners sont basiques et peuvent produire des faux positifs ou faux negatifs. Il n'est pas destine a remplacer des outils professionnels comme :
- Burp Suite Professional
- OWASP ZAP
- Nessus
- Metasploit

### Securite de l'application

- Mots de passe haches avec bcrypt
- Sessions securisees (httpOnly, SameSite)
- Validation des entrees utilisateur
- Permissions granulaires par investigation
- Upload de fichiers restreint (whitelist d'extensions)

---

## Auteurs

- Robin BRG
- Assistance : Claude (Anthropic)

## Licence

Projet educatif - MIT License

---

Cours : Python pour la Cyber - M1 2025-2026
Professeur : Tornier Alexandre

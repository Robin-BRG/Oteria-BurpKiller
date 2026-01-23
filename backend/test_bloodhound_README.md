# Fichier BloodHound de Test Complet

Ce fichier ZIP contient un scénario d'Active Directory vulnérable pour tester l'analyseur BloodHound.

## Contenu du ZIP

- `test_bloodhound_complete_users.json` - 10 utilisateurs
- `test_bloodhound_complete_computers.json` - 11 ordinateurs
- `test_bloodhound_complete_groups.json` - 10 groupes
- `test_bloodhound_complete_domains.json` - 1 domaine

## Domaine : CONTOSO.LOCAL

### Vulnérabilités incluses

#### Kerberoasting (3 comptes)
- **SVC_SQL@CONTOSO.LOCAL** - Compte service SQL avec SPN
- **SVC_WEB@CONTOSO.LOCAL** - Compte service Web avec SPN
- **SVC_REPL@CONTOSO.LOCAL** - Compte service de réplication avec SPN

#### AS-REP Roasting (2 comptes)
- **SVC_BACKUP@CONTOSO.LOCAL** - Pre-auth Kerberos désactivée + SPN (double vulnérabilité)
- **ADMIN_LEGACY@CONTOSO.LOCAL** - Pre-auth désactivée + compte admin + SID History

#### Delegation Non Contrainte
- **USER_DELEGATE@CONTOSO.LOCAL** - Utilisateur avec unconstrained delegation
- **WEB01.CONTOSO.LOCAL** - Serveur web avec unconstrained delegation (non-DC)

#### SID History
- **ADMIN_LEGACY@CONTOSO.LOCAL** - SID History du compte Administrator

#### OS Obsolètes
- **LEGACY-PC.CONTOSO.LOCAL** - Windows 7 Professional
- **OLDSERVER.CONTOSO.LOCAL** - Windows Server 2008 R2

#### DCSync
- **SVC_REPL@CONTOSO.LOCAL** - Droits GetChanges + GetChangesAll sur le domaine

#### ACL Abuse (Chemins d'attaque)

1. **HELPDESK → JOHN.DOE**
   - GenericAll sur JOHN.DOE
   - Permet contrôle total du compte

2. **IT_SUPPORT → JANE.SMITH**
   - ForceChangePassword
   - Peut forcer le changement de mot de passe

3. **HELPDESK → IT_SUPPORT**
   - WriteDacl sur IT_SUPPORT
   - Peut modifier les ACLs du compte

4. **HELPDESK → DNSADMINS**
   - WriteOwner sur le groupe DNSADMINS
   - Escalade possible vers DA

5. **EXCHANGE TRUSTED SUBSYSTEM → Domain**
   - GenericWrite sur le domaine
   - Vulnérabilité Exchange classique

#### LAPS
- **WEB02, FILE01, SQL01, BACKUP01, WORKSTATION01, WORKSTATION02** ont LAPS
- **HELPDESK** peut lire les passwords LAPS de plusieurs machines
- Chemin d'escalade possible

#### Groupes Privilégiés Surpeuplés
- **DOMAIN ADMINS** - 8 membres (seuil > 5)
- **BACKUP OPERATORS** - 8 membres (groupe privilégié)
- **ACCOUNT OPERATORS** - 3 membres
- **SERVER OPERATORS** - 3 membres

#### Configuration Domaine
- Niveau fonctionnel: **4** (Windows Server 2008 R2)
- Obsolète et devrait être élevé

## Chemins d'Attaque Potentiels

### Chemin 1: HELPDESK → Domain Admin
1. HELPDESK a WriteDacl sur IT_SUPPORT
2. IT_SUPPORT est dans ACCOUNT OPERATORS (groupe privilégié)
3. ACCOUNT OPERATORS peut créer des comptes dans certaines OUs
4. Escalade vers DA possible

### Chemin 2: Kerberoasting → Privilege Escalation
1. Kerberoast SVC_SQL@CONTOSO.LOCAL
2. SVC_SQL a AdminTo sur SQL01.CONTOSO.LOCAL
3. Pivot possible vers d'autres machines

### Chemin 3: DCSync Direct
1. Compromettre SVC_REPL@CONTOSO.LOCAL (Kerberoastable)
2. DCSync direct avec GetChangesAll
3. Dump tous les hashes du domaine

### Chemin 4: AS-REP Roast → DA
1. AS-REP Roast ADMIN_LEGACY@CONTOSO.LOCAL
2. Ce compte a SID History du compte Administrator
3. Accès DA via SID History

### Chemin 5: Exchange Exploitation
1. Compromettre EXCHANGE01.CONTOSO.LOCAL
2. EXCHANGE TRUSTED SUBSYSTEM a GenericWrite sur le domaine
3. PrivExchange → DCSync

## Statistiques Attendues

- **Users**: 10
- **Computers**: 11
- **Groups**: 10
- **Domains**: 1
- **Findings**: ~25-30 (selon la détection des ACLs)

## Findings par Sévérité Attendue

- **Critical**: ~5-7
  - DCSync capabilities
  - Unconstrained delegation
  - GenericAll/WriteDacl sur objets sensibles

- **High**: ~10-15
  - Kerberoasting
  - AS-REP Roasting
  - SID History
  - OS obsolètes
  - ACL abuse diverses

- **Medium**: ~5-10
  - Groupes privilégiés surpeuplés
  - Configuration domaine
  - AddMember sur groupes

## Comment Utiliser

1. Aller sur l'onglet **BloodHound** dans Active Directory
2. Cliquer sur **Upload BloodHound**
3. Sélectionner le fichier `test_bloodhound_complete.zip`
4. Attendre l'analyse (quelques secondes)
5. Explorer les findings par sévérité et catégorie

## Catégories de Findings

- `kerberoast` - Comptes Kerberoastables
- `asreproast` - Comptes AS-REP Roastables
- `delegation` - Unconstrained delegation
- `sid_history` - Comptes avec SID History
- `obsolete_os` - OS obsolètes
- `acl_abuse` - ACLs dangereuses
- `privileged_group` - Groupes privilégiés surpeuplés
- `domain_config` - Configuration domaine

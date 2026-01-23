# -*- coding: utf-8 -*-
"""
Module Active Directory - Enumeration LDAP, Kerberos, utilisateurs/groupes
+ Analyse BloodHound
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, ADScan, ADResult, BloodHoundAnalysis, BloodHoundFile, BloodHoundFinding
from datetime import datetime
from werkzeug.utils import secure_filename
import threading
import socket
import struct
import base64
import hashlib
import time
import json
import uuid
import os
import re
import zipfile
import tempfile

ad_bp = Blueprint('ad', __name__)

# Dossier pour les fichiers BloodHound
BLOODHOUND_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'bloodhound')
os.makedirs(BLOODHOUND_UPLOAD_FOLDER, exist_ok=True)


# ============================================================================
# PARSER BLOODHOUND JSON
# ============================================================================

class BloodHoundParser:
    """Parser pour fichiers BloodHound JSON"""

    # Relations dangereuses a detecter
    DANGEROUS_RELATIONS = {
        'GenericAll': {'severity': 'critical', 'description': 'Controle total sur l\'objet'},
        'GenericWrite': {'severity': 'high', 'description': 'Peut modifier les attributs de l\'objet'},
        'WriteOwner': {'severity': 'high', 'description': 'Peut changer le proprietaire de l\'objet'},
        'WriteDacl': {'severity': 'critical', 'description': 'Peut modifier les ACLs de l\'objet'},
        'AllExtendedRights': {'severity': 'high', 'description': 'Tous les droits etendus incluant DCSync'},
        'ForceChangePassword': {'severity': 'high', 'description': 'Peut forcer le changement de mot de passe'},
        'AddMember': {'severity': 'medium', 'description': 'Peut ajouter des membres au groupe'},
        'Owns': {'severity': 'critical', 'description': 'Proprietaire de l\'objet'},
        'DCSync': {'severity': 'critical', 'description': 'Peut repliquer les secrets du domaine'},
        'GetChanges': {'severity': 'high', 'description': 'Droit de replication partiel'},
        'GetChangesAll': {'severity': 'critical', 'description': 'Droit de replication complet (DCSync)'},
        'AdminTo': {'severity': 'critical', 'description': 'Admin local sur la machine'},
        'CanRDP': {'severity': 'medium', 'description': 'Peut se connecter en RDP'},
        'CanPSRemote': {'severity': 'medium', 'description': 'Peut utiliser PSRemote'},
        'ExecuteDCOM': {'severity': 'medium', 'description': 'Peut executer via DCOM'},
        'AllowedToDelegate': {'severity': 'high', 'description': 'Delegation Kerberos configuree'},
        'AllowedToAct': {'severity': 'high', 'description': 'Delegation basee sur les ressources'},
        'AddAllowedToAct': {'severity': 'high', 'description': 'Peut configurer RBCD'},
        'ReadLAPSPassword': {'severity': 'critical', 'description': 'Peut lire le mot de passe LAPS'},
        'ReadGMSAPassword': {'severity': 'critical', 'description': 'Peut lire le mot de passe gMSA'},
        'HasSIDHistory': {'severity': 'high', 'description': 'SID History permettant l\'usurpation'},
        'SQLAdmin': {'severity': 'high', 'description': 'Admin SQL Server'},
        'Contains': {'severity': 'info', 'description': 'Contient l\'objet (OU/Container)'},
        'GPLink': {'severity': 'info', 'description': 'GPO liee'},
    }

    # Groupes privilegies
    PRIVILEGED_GROUPS = [
        'DOMAIN ADMINS', 'ENTERPRISE ADMINS', 'SCHEMA ADMINS',
        'ADMINISTRATORS', 'ACCOUNT OPERATORS', 'BACKUP OPERATORS',
        'SERVER OPERATORS', 'PRINT OPERATORS', 'DNSADMINS',
        'DOMAIN CONTROLLERS', 'ENTERPRISE DOMAIN CONTROLLERS',
        'KEY ADMINS', 'ENTERPRISE KEY ADMINS', 'PROTECTED USERS',
        'CERT PUBLISHERS', 'REMOTE DESKTOP USERS', 'REMOTE MANAGEMENT USERS'
    ]

    def __init__(self):
        self.users = []
        self.computers = []
        self.groups = []
        self.domains = []
        self.gpos = []
        self.ous = []
        self.containers = []
        self.sessions = []
        self.findings = []
        self.domain_name = None

    def parse_file(self, filepath):
        """Parse un fichier BloodHound JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Detecter le type de fichier
        if isinstance(data, dict):
            if 'data' in data:
                # Format BloodHound v4+
                objects = data.get('data', [])
                meta = data.get('meta', {})
                file_type = meta.get('type', '').lower()
            else:
                # Fichier unique (domain, etc.)
                objects = [data]
                file_type = 'unknown'
        elif isinstance(data, list):
            objects = data
            file_type = self._detect_type(objects[0] if objects else {})
        else:
            return 'unknown', 0

        # Parser selon le type
        count = len(objects)
        for obj in objects:
            self._parse_object(obj, file_type)

        return file_type, count

    def _detect_type(self, obj):
        """Detecte le type d'objet BloodHound"""
        props = obj.get('Properties', obj.get('properties', {}))

        if 'samaccountname' in str(props).lower() and 'serviceprincipalnames' in str(props).lower():
            return 'users'
        elif 'operatingsystem' in str(props).lower():
            return 'computers'
        elif 'admincount' in str(props).lower() and 'samaccountname' in str(props).lower():
            return 'groups'
        elif 'functionallevel' in str(props).lower():
            return 'domains'
        elif 'gpcpath' in str(props).lower():
            return 'gpos'
        elif 'blocksinheritance' in str(props).lower():
            return 'ous'
        return 'unknown'

    def _parse_object(self, obj, file_type):
        """Parse un objet selon son type"""
        props = obj.get('Properties', obj.get('properties', {}))
        aces = obj.get('Aces', obj.get('aces', []))

        if file_type == 'users' or self._is_user(props):
            self._parse_user(obj, props, aces)
        elif file_type == 'computers' or self._is_computer(props):
            self._parse_computer(obj, props, aces)
        elif file_type == 'groups' or self._is_group(props):
            self._parse_group(obj, props, aces)
        elif file_type == 'domains' or self._is_domain(props):
            self._parse_domain(obj, props, aces)
        elif file_type == 'gpos':
            self.gpos.append(obj)
        elif file_type == 'ous':
            self.ous.append(obj)

    def _is_user(self, props):
        return 'samaccountname' in str(props).lower() and 'serviceprincipalnames' in str(props).lower()

    def _is_computer(self, props):
        return 'operatingsystem' in str(props).lower()

    def _is_group(self, props):
        return 'admincount' in str(props).lower() and not self._is_user(props)

    def _is_domain(self, props):
        return 'functionallevel' in str(props).lower()

    def _parse_user(self, obj, props, aces):
        """Parse un utilisateur et detecte les vulnerabilites"""
        user_data = {
            'name': props.get('name', props.get('samaccountname', 'Unknown')),
            'samaccountname': props.get('samaccountname', ''),
            'enabled': props.get('enabled', True),
            'admincount': props.get('admincount', False),
            'hasspn': props.get('hasspn', False),
            'dontreqpreauth': props.get('dontreqpreauth', False),
            'unconstraineddelegation': props.get('unconstraineddelegation', False),
            'pwdneverexpires': props.get('pwdneverexpires', False),
            'sensitive': props.get('sensitive', False),
            'sidhistory': props.get('sidhistory', []),
            'serviceprincipalnames': props.get('serviceprincipalnames', []),
            'aces': aces,
            'raw': obj
        }
        self.users.append(user_data)

        # Detecter Kerberoasting
        if user_data['hasspn'] and user_data['enabled']:
            self.findings.append({
                'category': 'kerberoast',
                'severity': 'high',
                'title': f"Kerberoastable: {user_data['name']}",
                'description': f"L'utilisateur {user_data['name']} a un SPN configure et peut etre Kerberoaste.",
                'affected_objects': {'user': user_data['name'], 'spns': user_data['serviceprincipalnames']},
                'recommendation': 'Utiliser des mots de passe forts (25+ caracteres) pour les comptes de service ou migrer vers gMSA.',
                'references': [{'name': 'MITRE ATT&CK', 'id': 'T1558.003'}]
            })

        # Detecter AS-REP Roasting
        if user_data['dontreqpreauth'] and user_data['enabled']:
            self.findings.append({
                'category': 'asreproast',
                'severity': 'high',
                'title': f"AS-REP Roastable: {user_data['name']}",
                'description': f"L'utilisateur {user_data['name']} n'a pas de pre-authentification Kerberos requise.",
                'affected_objects': {'user': user_data['name']},
                'recommendation': 'Activer la pre-authentification Kerberos pour ce compte.',
                'references': [{'name': 'MITRE ATT&CK', 'id': 'T1558.004'}]
            })

        # Detecter delegation non contrainte
        if user_data['unconstraineddelegation'] and user_data['enabled']:
            self.findings.append({
                'category': 'delegation',
                'severity': 'critical',
                'title': f"Unconstrained Delegation: {user_data['name']}",
                'description': f"L'utilisateur {user_data['name']} a une delegation non contrainte, permettant de capturer des TGT.",
                'affected_objects': {'user': user_data['name']},
                'recommendation': 'Remplacer par une delegation contrainte ou basee sur les ressources.',
                'references': [{'name': 'MITRE ATT&CK', 'id': 'T1558.001'}]
            })

        # Detecter SID History
        if user_data['sidhistory']:
            self.findings.append({
                'category': 'sid_history',
                'severity': 'high',
                'title': f"SID History: {user_data['name']}",
                'description': f"L'utilisateur {user_data['name']} a un SID History qui peut etre abuse.",
                'affected_objects': {'user': user_data['name'], 'sidhistory': user_data['sidhistory']},
                'recommendation': 'Supprimer le SID History si non necessaire.',
                'references': [{'name': 'MITRE ATT&CK', 'id': 'T1134.005'}]
            })

    def _parse_computer(self, obj, props, aces):
        """Parse un ordinateur et detecte les vulnerabilites"""
        computer_data = {
            'name': props.get('name', 'Unknown'),
            'operatingsystem': props.get('operatingsystem', ''),
            'enabled': props.get('enabled', True),
            'unconstraineddelegation': props.get('unconstraineddelegation', False),
            'allowedtodelegate': props.get('allowedtodelegate', []),
            'haslaps': props.get('haslaps', False),
            'aces': aces,
            'raw': obj
        }
        self.computers.append(computer_data)

        # Detecter delegation non contrainte sur les machines
        if computer_data['unconstraineddelegation'] and computer_data['enabled']:
            if 'DOMAIN CONTROLLER' not in computer_data['name'].upper():
                self.findings.append({
                    'category': 'delegation',
                    'severity': 'critical',
                    'title': f"Unconstrained Delegation: {computer_data['name']}",
                    'description': f"La machine {computer_data['name']} a une delegation non contrainte.",
                    'affected_objects': {'computer': computer_data['name']},
                    'recommendation': 'Supprimer la delegation non contrainte sur les serveurs non-DC.',
                    'references': [{'name': 'MITRE ATT&CK', 'id': 'T1558.001'}]
                })

        # Detecter OS obsolete
        os_name = computer_data['operatingsystem'].lower() if computer_data['operatingsystem'] else ''
        if any(old in os_name for old in ['2003', '2008', 'xp', 'vista', 'windows 7']):
            self.findings.append({
                'category': 'obsolete_os',
                'severity': 'high',
                'title': f"OS Obsolete: {computer_data['name']}",
                'description': f"La machine {computer_data['name']} utilise un OS obsolete: {computer_data['operatingsystem']}",
                'affected_objects': {'computer': computer_data['name'], 'os': computer_data['operatingsystem']},
                'recommendation': 'Mettre a jour vers un systeme d\'exploitation supporte.',
                'references': []
            })

    def _parse_group(self, obj, props, aces):
        """Parse un groupe et detecte les vulnerabilites"""
        group_data = {
            'name': props.get('name', 'Unknown'),
            'samaccountname': props.get('samaccountname', ''),
            'admincount': props.get('admincount', False),
            'members': obj.get('Members', obj.get('members', [])),
            'aces': aces,
            'raw': obj
        }
        self.groups.append(group_data)

        # Verifier si c'est un groupe privilegie avec beaucoup de membres
        group_upper = group_data['name'].upper()
        for priv_group in self.PRIVILEGED_GROUPS:
            if priv_group in group_upper:
                member_count = len(group_data['members'])
                if member_count > 5:
                    self.findings.append({
                        'category': 'privileged_group',
                        'severity': 'medium',
                        'title': f"Groupe privilegie surpeuple: {group_data['name']}",
                        'description': f"Le groupe privilegie {group_data['name']} contient {member_count} membres.",
                        'affected_objects': {'group': group_data['name'], 'member_count': member_count},
                        'recommendation': 'Reduire le nombre de membres dans les groupes privilegies.',
                        'references': []
                    })
                break

    def _parse_domain(self, obj, props, aces):
        """Parse un domaine"""
        domain_data = {
            'name': props.get('name', 'Unknown'),
            'functionallevel': props.get('functionallevel', ''),
            'aces': aces,
            'raw': obj
        }
        self.domains.append(domain_data)
        if not self.domain_name:
            self.domain_name = domain_data['name']

        # Verifier le niveau fonctionnel
        level = domain_data['functionallevel']
        if level and int(level) < 7:  # Windows Server 2016
            level_names = {
                0: 'Windows 2000', 1: 'Windows 2003 Mixed', 2: 'Windows 2003',
                3: 'Windows 2008', 4: 'Windows 2008 R2', 5: 'Windows 2012',
                6: 'Windows 2012 R2', 7: 'Windows 2016'
            }
            level_name = level_names.get(int(level), f'Level {level}')
            self.findings.append({
                'category': 'domain_config',
                'severity': 'medium',
                'title': f"Niveau fonctionnel du domaine bas: {level_name}",
                'description': f"Le domaine {domain_data['name']} est au niveau fonctionnel {level_name}.",
                'affected_objects': {'domain': domain_data['name'], 'level': level_name},
                'recommendation': 'Elever le niveau fonctionnel du domaine si possible.',
                'references': []
            })

    def analyze_acls(self):
        """Analyse les ACLs pour trouver des chemins d'attaque"""
        all_objects = self.users + self.computers + self.groups + self.domains

        for obj in all_objects:
            obj_name = obj.get('name', 'Unknown')
            aces = obj.get('aces', [])

            for ace in aces:
                right_name = ace.get('RightName', ace.get('rightname', ''))
                principal_name = ace.get('PrincipalName', ace.get('principalname', ''))
                principal_type = ace.get('PrincipalType', ace.get('principaltype', ''))

                if right_name in self.DANGEROUS_RELATIONS:
                    rel_info = self.DANGEROUS_RELATIONS[right_name]

                    # Ignorer certaines relations normales
                    if principal_name.upper() in ['DOMAIN ADMINS', 'ENTERPRISE ADMINS', 'ADMINISTRATORS']:
                        continue

                    self.findings.append({
                        'category': 'acl_abuse',
                        'severity': rel_info['severity'],
                        'title': f"{right_name}: {principal_name} -> {obj_name}",
                        'description': f"{principal_name} ({principal_type}) a le droit {right_name} sur {obj_name}. {rel_info['description']}",
                        'affected_objects': {
                            'source': principal_name,
                            'target': obj_name,
                            'relation': right_name
                        },
                        'attack_path': [principal_name, right_name, obj_name],
                        'recommendation': f"Verifier si {principal_name} a reellement besoin de ce droit sur {obj_name}.",
                        'references': []
                    })

    def get_statistics(self):
        """Retourne les statistiques de l'analyse"""
        return {
            'users_count': len(self.users),
            'computers_count': len(self.computers),
            'groups_count': len(self.groups),
            'domains_count': len(self.domains),
            'gpos_count': len(self.gpos),
            'ous_count': len(self.ous),
            'findings_count': len(self.findings),
            'domain': self.domain_name
        }

    def get_findings_summary(self):
        """Retourne un resume des findings par severite"""
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for f in self.findings:
            sev = f.get('severity', 'info')
            summary[sev] = summary.get(sev, 0) + 1
        return summary


# ============================================================================
# OUTILS ACTIVE DIRECTORY
# ============================================================================

# Ports AD communs
AD_PORTS = {
    88: 'Kerberos',
    389: 'LDAP',
    636: 'LDAPS',
    445: 'SMB',
    135: 'MSRPC',
    139: 'NetBIOS',
    3268: 'LDAP Global Catalog',
    3269: 'LDAPS Global Catalog',
    5985: 'WinRM HTTP',
    5986: 'WinRM HTTPS',
    9389: 'AD Web Services'
}

# Attributs LDAP interessants
LDAP_USER_ATTRS = [
    'sAMAccountName', 'userPrincipalName', 'displayName', 'mail',
    'memberOf', 'userAccountControl', 'lastLogon', 'pwdLastSet',
    'adminCount', 'servicePrincipalName', 'description'
]

LDAP_GROUP_ATTRS = [
    'sAMAccountName', 'distinguishedName', 'member', 'memberOf',
    'adminCount', 'description', 'groupType'
]

# Groupes privilegies a detecter
PRIVILEGED_GROUPS = [
    'Domain Admins', 'Enterprise Admins', 'Schema Admins',
    'Administrators', 'Account Operators', 'Backup Operators',
    'Server Operators', 'Print Operators', 'DnsAdmins',
    'Remote Desktop Users', 'Group Policy Creator Owners'
]


def check_ad_ports(target, timeout=3):
    """Verifier les ports AD ouverts sur une cible"""
    open_ports = []

    for port, service in AD_PORTS.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            sock.close()

            if result == 0:
                open_ports.append({
                    'port': port,
                    'service': service,
                    'state': 'open'
                })
        except Exception:
            pass

    return open_ports


def enumerate_ldap_anonymous(target, port=389, timeout=5):
    """
    Tenter une enumeration LDAP anonyme
    Retourne les infos de base du domaine si disponible
    """
    results = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target, port))

        # Construction d'une requete LDAP simple (RootDSE query)
        # Sequence LDAP pour interroger le RootDSE
        ldap_search = bytes([
            0x30, 0x25,  # SEQUENCE
            0x02, 0x01, 0x01,  # messageID: 1
            0x63, 0x20,  # searchRequest
            0x04, 0x00,  # baseObject: ""
            0x0a, 0x01, 0x00,  # scope: baseObject
            0x0a, 0x01, 0x00,  # derefAliases: neverDerefAliases
            0x02, 0x01, 0x00,  # sizeLimit: 0
            0x02, 0x01, 0x00,  # timeLimit: 0
            0x01, 0x01, 0x00,  # typesOnly: false
            0x87, 0x0b, 0x6f, 0x62, 0x6a, 0x65, 0x63, 0x74,
            0x63, 0x6c, 0x61, 0x73, 0x73,  # filter: objectclass
            0x30, 0x00  # attributes: all
        ])

        sock.send(ldap_search)
        response = sock.recv(4096)
        sock.close()

        if response:
            # Parser la reponse (simplifie)
            response_str = response.decode('utf-8', errors='ignore')

            # Chercher des infos interessantes
            patterns = {
                'domainFunctionality': r'domainFunctionality[^\x00]*',
                'forestFunctionality': r'forestFunctionality[^\x00]*',
                'defaultNamingContext': r'DC=[^,\x00]+(?:,DC=[^,\x00]+)*',
                'dnsHostName': r'[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-.]+',
            }

            for name, pattern in patterns.items():
                matches = re.findall(pattern, response_str)
                if matches:
                    results.append({
                        'type': 'ldap_info',
                        'name': name,
                        'value': matches[0][:200],
                        'severity': 'info'
                    })

            if results:
                results.append({
                    'type': 'vulnerability',
                    'name': 'LDAP Anonymous Bind',
                    'value': 'Anonymous LDAP access is enabled',
                    'severity': 'medium',
                    'description': 'Le serveur LDAP accepte les connexions anonymes, permettant l\'enumeration du domaine.'
                })

    except Exception as e:
        pass

    return results


def check_null_session(target, timeout=5):
    """Verifier si les sessions NULL sont autorisees (SMB)"""
    results = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target, 445))

        # SMB Negotiate Protocol Request (simplifie)
        negotiate = bytes([
            0x00, 0x00, 0x00, 0x85,  # NetBIOS length
            0xff, 0x53, 0x4d, 0x42,  # SMB magic
            0x72,  # Negotiate Protocol
            0x00, 0x00, 0x00, 0x00,  # Status
            0x18,  # Flags
            0x53, 0xc8,  # Flags2
            0x00, 0x00,  # PID High
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Signature
            0x00, 0x00,  # Reserved
            0x00, 0x00,  # TID
            0x00, 0x00,  # PID
            0x00, 0x00,  # UID
            0x00, 0x00,  # MID
            0x00,  # Word Count
            0x62, 0x00,  # Byte Count
            0x02, 0x50, 0x43, 0x20, 0x4e, 0x45, 0x54, 0x57,
            0x4f, 0x52, 0x4b, 0x20, 0x50, 0x52, 0x4f, 0x47,
            0x52, 0x41, 0x4d, 0x20, 0x31, 0x2e, 0x30, 0x00
        ])

        sock.send(negotiate)
        response = sock.recv(1024)
        sock.close()

        if response and len(response) > 36:
            # Verifier si la reponse indique un succes
            if response[9:13] == b'\x00\x00\x00\x00':
                results.append({
                    'type': 'smb_info',
                    'name': 'SMB Accessible',
                    'value': 'SMB service is responding',
                    'severity': 'info'
                })

    except Exception:
        pass

    return results


def enumerate_users_rpc(target, timeout=10):
    """Enumeration des utilisateurs via RPC (si autorise)"""
    results = []
    try:
        from impacket.dcerpc.v5 import transport, samr
        from impacket.dcerpc.v5.dtypes import NULL

        # Tenter une connexion anonyme (Null Session) sur le pipe SAMR
        binding = r'ncacn_np:%s[\pipe\samr]' % target
        rpctransport = transport.DCERPCTransportFactory(binding)
        rpctransport.set_connect_timeout(timeout)

        try:
            dce = rpctransport.get_dce_rpc()
            dce.connect()
            dce.bind(samr.MSRPC_UUID_SAMR)
            
            # Connexion (Anonyme/Null Session)
            resp = samr.hSamrConnect2(dce)
            serverHandle = resp['ServerHandle']

            # Enumerer les domaines
            resp = samr.hSamrEnumerateDomainsInSamServer(dce, serverHandle)
            domains = resp['Buffer']['Buffer']

            for domain in domains:
                domainName = domain['Name']
                results.append({
                    'type': 'ad_info',
                    'name': 'RPC Domain',
                    'value': domainName,
                    'severity': 'info'
                })

                # Lookup Domain SID
                resp = samr.hSamrLookupDomainInSamServer(dce, serverHandle, domainName)
                domainId = resp['DomainId']

                # Ouvrir le domaine
                resp = samr.hSamrOpenDomain(dce, serverHandle, domainId=domainId)
                domainHandle = resp['DomainHandle']

                # Enumerer les utilisateurs
                resp = samr.hSamrEnumerateUsersInDomain(dce, domainHandle)
                for user in resp['Buffer']['Buffer']:
                    results.append({
                        'type': 'user',
                        'name': user['Name'],
                        'value': f"RID: {user['RelativeId']}",
                        'severity': 'info'
                    })

        except Exception:
            pass  # Echec de connexion ou acces refuse (normal si securise)

    except ImportError:
        pass
    except Exception:
        pass

    return results


def check_kerberos(target, timeout=5):
    """Verifier le service Kerberos"""
    results = []

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target, 88))

        # Le simple fait de se connecter indique que Kerberos est accessible
        results.append({
            'type': 'kerberos_info',
            'name': 'Kerberos Service',
            'value': 'Kerberos is accessible on port 88',
            'severity': 'info'
        })

        # On pourrait ici tenter un AS-REQ pour verifier si pre-auth est requis
        # Cela necessite une implementation plus complexe du protocole Kerberos

        sock.close()

    except Exception:
        pass

    return results


def scan_ad(target, scan_type='basic', progress_callback=None):
    """
    Scanner un controleur de domaine Active Directory - VERSION COMPLETE

    Args:
        target: IP ou hostname du DC
        scan_type: 'basic' (ports + LDAP), 'full' (+ SMB + Kerberos + DNS + NetBIOS + vulnerabilites)
        progress_callback: fonction(current, total) pour le suivi

    Returns:
        Liste de resultats avec analyse de vulnerabilites
    """
    all_results = []
    steps = 8 if scan_type == 'full' else 3
    current = 0

    # Etape 1: Scan des ports AD
    if progress_callback:
        progress_callback(current, steps)
    current += 1

    ports = check_ad_ports(target)
    for p in ports:
        all_results.append({
            'type': 'port',
            'name': f"Port {p['port']} ({p['service']})",
            'value': p['state'],
            'severity': 'info',
            'port': p['port'],
            'service': p['service']
        })

    # Etape 2: Enumeration DNS
    if progress_callback:
        progress_callback(current, steps)
    current += 1

    dns_results = enumerate_dns(target)
    all_results.extend(dns_results)

    # Etape 3: Enumeration LDAP anonyme
    if progress_callback:
        progress_callback(current, steps)
    current += 1

    ldap_port = 389 if any(p['port'] == 389 for p in ports) else None
    if ldap_port:
        ldap_results = enumerate_ldap_anonymous(target, ldap_port)
        all_results.extend(ldap_results)

    if scan_type == 'full':
        # Etape 4: Enumeration NetBIOS
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        netbios_results = enumerate_netbios(target)
        all_results.extend(netbios_results)

        # Etape 5: Verification SMB
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        if any(p['port'] == 445 for p in ports):
            smb_results = check_null_session(target)
            all_results.extend(smb_results)

        # Etape 6: Verification Kerberos
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        if any(p['port'] == 88 for p in ports):
            krb_results = check_kerberos(target)
            all_results.extend(krb_results)

        # Etape 7: Enumeration RPC (Users/Groups)
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        if any(p['port'] == 445 for p in ports):
            rpc_results = enumerate_users_rpc(target)
            all_results.extend(rpc_results)

        # Etape 8: Analyse des vulnerabilites
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        vulnerabilities = analyze_ad_vulnerabilities(all_results)
        all_results.extend(vulnerabilities)

    if progress_callback:
        progress_callback(steps, steps)

    return all_results


def enumerate_dns(target, timeout=3):
    """Enumerer les informations DNS pour detecter le domaine"""
    results = []
    try:
        import socket
        # Tenter de recuperer le FQDN
        try:
            fqdn = socket.getfqdn(target)
            if fqdn != target and '.' in fqdn:
                results.append({
                    'type': 'dns_info',
                    'name': 'FQDN',
                    'value': fqdn,
                    'severity': 'info'
                })
                # Extraire le domaine
                parts = fqdn.split('.')
                if len(parts) >= 2:
                    domain = '.'.join(parts[-2:])
                    results.append({
                        'type': 'dns_info',
                        'name': 'Possible Domain',
                        'value': domain,
                        'severity': 'info'
                    })
        except:
            pass

        # Tenter reverse DNS
        try:
            hostinfo = socket.gethostbyaddr(target)
            if hostinfo and hostinfo[0]:
                results.append({
                    'type': 'dns_info',
                    'name': 'Reverse DNS',
                    'value': hostinfo[0],
                    'severity': 'info'
                })
        except:
            pass
    except:
        pass

    return results


def enumerate_netbios(target, timeout=3):
    """Enumerer les informations NetBIOS"""
    results = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # NetBIOS Name Query
        query = bytes([
            0x80, 0x94,  # Transaction ID
            0x00, 0x00,  # Flags
            0x00, 0x01,  # Questions
            0x00, 0x00,  # Answer RRs
            0x00, 0x00,  # Authority RRs
            0x00, 0x00,  # Additional RRs
            0x20, 0x43, 0x4b, 0x41, 0x41, 0x41, 0x41, 0x41,
            0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
            0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
            0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
            0x41, 0x41, 0x00,  # Name
            0x00, 0x21,  # Type: NBSTAT
            0x00, 0x01   # Class: IN
        ])

        sock.sendto(query, (target, 137))
        data, _ = sock.recvfrom(4096)
        sock.close()

        if data and len(data) > 56:
            # Parser la reponse NetBIOS
            num_names = data[56]
            offset = 57

            for i in range(min(num_names, 10)):
                if offset + 18 <= len(data):
                    name = data[offset:offset+15].decode('ascii', errors='ignore').strip()
                    name_type = data[offset+15]
                    flags = struct.unpack('>H', data[offset+16:offset+18])[0]

                    if name:
                        results.append({
                            'type': 'netbios_info',
                            'name': f'NetBIOS Name ({hex(name_type)})',
                            'value': name,
                            'severity': 'info'
                        })

                    offset += 18
    except:
        pass

    return results


def analyze_ad_vulnerabilities(scan_results):
    """Analyser les resultats du scan pour detecter des vulnerabilites AD"""
    vulnerabilities = []

    # Analyser les ports ouverts
    open_ports = [r for r in scan_results if r.get('type') == 'port']
    port_numbers = [p['port'] for p in open_ports]

    # SMB Signing
    if 445 in port_numbers:
        vulnerabilities.append({
            'type': 'vulnerability',
            'name': 'SMB Service Detected',
            'value': 'Port 445 ouvert',
            'severity': 'medium',
            'description': 'Le service SMB est accessible. Verifier si SMB signing est requis.',
            'recommendation': 'Activer "Require SMB Signing" sur le DC pour prevenir les attaques relay.',
            'mitre_id': 'T1187'
        })

    # LDAP non-secure
    if 389 in port_numbers and 636 not in port_numbers:
        vulnerabilities.append({
            'type': 'vulnerability',
            'name': 'LDAP without LDAPS',
            'value': 'LDAP non-chiffre disponible',
            'severity': 'high',
            'description': 'LDAP est accessible sans chiffrement (pas de LDAPS sur 636).',
            'recommendation': 'Configurer LDAPS et desactiver LDAP non-chiffre.',
            'mitre_id': 'T1071.004'
        })

    # Kerberos pre-auth
    if 88 in port_numbers:
        vulnerabilities.append({
            'type': 'info',
            'name': 'Kerberos Service Active',
            'value': 'Port 88 ouvert',
            'severity': 'info',
            'description': 'Service Kerberos accessible. Vulnerable aux attaques Kerberoasting et AS-REP Roasting si mal configure.',
            'recommendation': 'S\'assurer que tous les comptes requirent la pre-authentification Kerberos.'
        })

    # LDAP Anonymous Bind
    ldap_anon = [r for r in scan_results if r.get('name') == 'LDAP Anonymous Bind']
    if ldap_anon:
        vulnerabilities.append({
            'type': 'vulnerability',
            'name': 'LDAP Anonymous Bind Enabled',
            'value': 'Connexion anonyme LDAP autorisee',
            'severity': 'high',
            'description': 'Le serveur LDAP accepte les connexions anonymes, permettant l\'enumeration complete du domaine sans authentification.',
            'recommendation': 'Desactiver les connexions anonymes LDAP dans la GPO.',
            'mitre_id': 'T1087.002'
        })

    return vulnerabilities


def generate_bloodhound_commands(target, domain=None):
    """Generer des commandes BloodHound pour l'enumeration"""
    commands = []

    # SharpHound
    if domain:
        commands.append({
            'tool': 'SharpHound',
            'description': 'Collection BloodHound depuis Windows (avec credentials)',
            'command': f'SharpHound.exe -c All -d {domain} --ldapusername USER --ldappassword PASS'
        })
        commands.append({
            'tool': 'SharpHound',
            'description': 'Collection BloodHound depuis Windows (contexte actuel)',
            'command': f'SharpHound.exe -c All -d {domain}'
        })
    else:
        commands.append({
            'tool': 'SharpHound',
            'description': 'Collection BloodHound depuis Windows',
            'command': 'SharpHound.exe -c All'
        })

    # BloodHound.py
    if domain and target:
        commands.append({
            'tool': 'bloodhound-python',
            'description': 'Collection BloodHound depuis Linux',
            'command': f'bloodhound-python -u USER -p PASS -d {domain} -dc {target} -c All --zip'
        })
    elif target:
        commands.append({
            'tool': 'bloodhound-python',
            'description': 'Collection BloodHound depuis Linux',
            'command': f'bloodhound-python -u USER -p PASS -ns {target} -c All --zip'
        })

    # Enumeration alternative
    commands.append({
        'tool': 'ldapdomaindump',
        'description': 'Dump LDAP pour analyse manuelle',
        'command': f'ldapdomaindump -u "DOMAIN\\USER" -p PASS {target}'
    })

    commands.append({
        'tool': 'crackmapexec',
        'description': 'Enumeration SMB et utilisateurs',
        'command': f'crackmapexec smb {target} -u USER -p PASS --users --groups --shares'
    })

    return commands


def detect_dc(target):
    """Detecter si une cible est probablement un controleur de domaine - VERSION COMPLETE"""
    dc_indicators = []
    score = 0
    domain_info = {}

    # Etape 1: Scan des ports AD
    ports = check_ad_ports(target)
    port_numbers = [p['port'] for p in ports]

    # Criteres de detection
    if 88 in port_numbers:
        score += 3
        dc_indicators.append('Kerberos (88)')
    if 389 in port_numbers:
        score += 2
        dc_indicators.append('LDAP (389)')
    if 636 in port_numbers:
        score += 2
        dc_indicators.append('LDAPS (636)')
    if 445 in port_numbers:
        score += 1
        dc_indicators.append('SMB (445)')
    if 3268 in port_numbers:
        score += 3
        dc_indicators.append('Global Catalog (3268)')
    if 9389 in port_numbers:
        score += 2
        dc_indicators.append('AD Web Services (9389)')

    is_dc = score >= 5

    # Etape 2: Enumeration DNS
    dns_results = enumerate_dns(target)
    for r in dns_results:
        if r['name'] == 'Possible Domain':
            domain_info['domain'] = r['value']
        elif r['name'] == 'FQDN':
            domain_info['fqdn'] = r['value']

    # Etape 3: Enumeration NetBIOS
    netbios_results = enumerate_netbios(target)
    if netbios_results:
        domain_info['netbios_names'] = [r['value'] for r in netbios_results]

    # Etape 4: LDAP enumeration si AD detecte
    ldap_results = []
    if is_dc and 389 in port_numbers:
        ldap_results = enumerate_ldap_anonymous(target, 389)
        for r in ldap_results:
            if 'DC=' in r.get('value', ''):
                # Extraire le nom de domaine du DN
                dn = r['value']
                domain_parts = re.findall(r'DC=([^,\x00]+)', dn)
                if domain_parts:
                    domain_info['domain_dn'] = '.'.join(domain_parts)

    return {
        'is_dc': is_dc,
        'confidence': min(score * 10, 100),
        'indicators': dc_indicators,
        'open_ports': ports,
        'domain_info': domain_info,
        'dns_results': dns_results,
        'netbios_results': netbios_results,
        'ldap_results': ldap_results,
        'detected_domain': domain_info.get('domain') or domain_info.get('domain_dn'),
        'recommendations': generate_bloodhound_commands(
            target,
            domain_info.get('domain') or domain_info.get('domain_dn')
        ) if is_dc else []
    }


# ============================================================================
# ROUTES API
# ============================================================================

@ad_bp.route('/api/investigations/<int:inv_id>/ad-scans', methods=['POST'])
@login_required
def start_ad_scan(inv_id):
    """Lancer un scan Active Directory"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json() or {}
    target = data.get('target', '')
    scan_type = data.get('scan_type', 'basic')  # basic, full
    domain = data.get('domain', '')
    username = data.get('username', '')
    password = data.get('password', '')

    if not target:
        # Extraire l'hote de l'URL cible
        from urllib.parse import urlparse
        parsed = urlparse(investigation.target_url)
        target = parsed.hostname or parsed.netloc

    if not target:
        return jsonify({'error': 'Cible non specifiee'}), 400

    # Creer le scan
    scan = ADScan(
        investigation_id=inv_id,
        started_by_id=current_user.id,
        target=target,
        domain=domain,
        scan_type=scan_type,
        status='running'
    )
    db.session.add(scan)
    db.session.commit()

    # Lancer le scan en arriere-plan
    def run_scan():
        from app import app
        with app.app_context():
            try:
                scan_obj = db.session.get(ADScan, scan.id)

                def progress_callback(current, total):
                    scan_obj.progress_current = current
                    scan_obj.progress_total = total
                    db.session.commit()

                # D'abord detecter si c'est un DC avec detection complete
                dc_detection = detect_dc(target)

                if dc_detection['is_dc']:
                    # C'est probablement un DC, on ajoute l'info detaillee
                    result = ADResult(
                        scan_id=scan_obj.id,
                        result_type='detection',
                        name='Domain Controller Detected',
                        value=f"Confidence: {dc_detection['confidence']}%",
                        severity='info',
                        description=f"Indicators: {', '.join(dc_detection['indicators'])}"
                    )
                    db.session.add(result)

                    # Ajouter le domaine detecte si disponible
                    if dc_detection.get('detected_domain'):
                        result = ADResult(
                            scan_id=scan_obj.id,
                            result_type='domain_info',
                            name='Domain Detected',
                            value=dc_detection['detected_domain'],
                            severity='info',
                            description='Nom de domaine Active Directory detecte'
                        )
                        db.session.add(result)

                    # Ajouter les recommandations BloodHound
                    if dc_detection.get('recommendations'):
                        for idx, rec in enumerate(dc_detection['recommendations'][:3]):
                            result = ADResult(
                                scan_id=scan_obj.id,
                                result_type='recommendation',
                                name=f"BloodHound Collection - {rec['tool']}",
                                value=rec['command'],
                                severity='info',
                                description=rec['description']
                            )
                            db.session.add(result)

                # Lancer le scan AD complet
                results = scan_ad(target, scan_type, progress_callback)

                # Sauvegarder les resultats
                for r in results:
                    result = ADResult(
                        scan_id=scan_obj.id,
                        result_type=r.get('type', 'info'),
                        name=r.get('name', ''),
                        value=r.get('value', ''),
                        severity=r.get('severity', 'info'),
                        port=r.get('port'),
                        service=r.get('service'),
                        description=r.get('description') or r.get('recommendation', '')
                    )
                    db.session.add(result)

                scan_obj.status = 'completed'
                scan_obj.completed_at = datetime.utcnow()
                db.session.commit()

            except Exception as e:
                scan_obj = db.session.get(ADScan, scan.id)
                if scan_obj:
                    scan_obj.status = 'failed'
                    scan_obj.error_message = str(e)
                    db.session.commit()

    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

    return jsonify(scan.to_dict()), 201


@ad_bp.route('/api/investigations/<int:inv_id>/ad-scans', methods=['GET'])
@login_required
def list_ad_scans(inv_id):
    """Lister les scans AD d'une investigation"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    scans = ADScan.query.filter_by(investigation_id=inv_id).order_by(ADScan.created_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])


@ad_bp.route('/api/ad-scans/<int:scan_id>', methods=['GET'])
@login_required
def get_ad_scan(scan_id):
    """Obtenir le statut d'un scan AD"""
    scan = ADScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    return jsonify(scan.to_dict())


@ad_bp.route('/api/ad-scans/<int:scan_id>/results', methods=['GET'])
@login_required
def get_ad_results(scan_id):
    """Obtenir les resultats d'un scan AD"""
    scan = ADScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    results = ADResult.query.filter_by(scan_id=scan_id).all()
    return jsonify({
        'scan': scan.to_dict(),
        'results': [r.to_dict() for r in results]
    })


@ad_bp.route('/api/investigations/<int:inv_id>/detect-dc', methods=['POST'])
@login_required
def api_detect_dc(inv_id):
    """Detecter si une cible est un DC"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json() or {}
    target = data.get('target', '')

    if not target:
        from urllib.parse import urlparse
        parsed = urlparse(investigation.target_url)
        target = parsed.hostname or parsed.netloc

    if not target:
        return jsonify({'error': 'Cible non specifiee'}), 400

    result = detect_dc(target)
    return jsonify(result)


# ============================================================================
# ROUTES API BLOODHOUND
# ============================================================================

@ad_bp.route('/api/investigations/<int:inv_id>/bloodhound', methods=['POST'])
@login_required
def upload_bloodhound(inv_id):
    """
    Upload de fichiers BloodHound (JSON ou ZIP)
    Lance automatiquement l'analyse apres l'upload
    """
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    if 'files' not in request.files and 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    # Recuperer les fichiers (support single ou multiple)
    files = request.files.getlist('files') or [request.files.get('file')]
    files = [f for f in files if f and f.filename]

    if not files:
        return jsonify({'error': 'Aucun fichier valide'}), 400

    # Creer l'analyse
    analysis_name = request.form.get('name', f'Analyse BloodHound {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')
    analysis = BloodHoundAnalysis(
        investigation_id=inv_id,
        started_by_id=current_user.id,
        name=analysis_name,
        status='running'
    )
    db.session.add(analysis)
    db.session.commit()

    # Creer un dossier pour cette analyse
    analysis_folder = os.path.join(BLOODHOUND_UPLOAD_FOLDER, str(analysis.id))
    os.makedirs(analysis_folder, exist_ok=True)

    uploaded_files = []
    json_files = []

    for file in files:
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = os.path.join(analysis_folder, unique_filename)
        file.save(file_path)

        # Si c'est un ZIP, extraire les fichiers JSON
        if extension == 'zip':
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    for zip_info in zip_ref.infolist():
                        if zip_info.filename.endswith('.json'):
                            extracted_path = zip_ref.extract(zip_info, analysis_folder)
                            json_files.append(extracted_path)

                            # Creer un enregistrement pour chaque fichier extrait
                            bh_file = BloodHoundFile(
                                analysis_id=analysis.id,
                                filename=os.path.basename(extracted_path),
                                original_filename=zip_info.filename,
                                file_size=zip_info.file_size
                            )
                            db.session.add(bh_file)
                            uploaded_files.append(bh_file)
            except zipfile.BadZipFile:
                analysis.status = 'failed'
                analysis.error_message = 'Fichier ZIP invalide'
                db.session.commit()
                return jsonify({'error': 'Fichier ZIP invalide'}), 400
        elif extension == 'json':
            json_files.append(file_path)
            file_size = os.path.getsize(file_path)

            bh_file = BloodHoundFile(
                analysis_id=analysis.id,
                filename=unique_filename,
                original_filename=original_filename,
                file_size=file_size
            )
            db.session.add(bh_file)
            uploaded_files.append(bh_file)
        else:
            continue

    db.session.commit()

    if not json_files:
        analysis.status = 'failed'
        analysis.error_message = 'Aucun fichier JSON BloodHound trouve'
        db.session.commit()
        return jsonify({'error': 'Aucun fichier JSON BloodHound trouve'}), 400

    # Lancer l'analyse en arriere-plan
    def run_analysis():
        from app import app
        with app.app_context():
            try:
                analysis_obj = db.session.get(BloodHoundAnalysis, analysis.id)
                parser = BloodHoundParser()

                # Parser tous les fichiers
                for json_file in json_files:
                    try:
                        file_type, count = parser.parse_file(json_file)

                        # Mettre a jour le type de fichier dans la DB
                        bh_file = BloodHoundFile.query.filter_by(
                            analysis_id=analysis.id,
                            filename=os.path.basename(json_file)
                        ).first()
                        if bh_file:
                            bh_file.file_type = file_type
                            bh_file.objects_count = count
                    except json.JSONDecodeError as e:
                        continue
                    except Exception as e:
                        continue

                # Analyser les ACLs
                parser.analyze_acls()

                # Mettre a jour les statistiques
                stats = parser.get_statistics()
                analysis_obj.domain = stats['domain']
                analysis_obj.users_count = stats['users_count']
                analysis_obj.computers_count = stats['computers_count']
                analysis_obj.groups_count = stats['groups_count']
                analysis_obj.domains_count = stats['domains_count']

                # Sauvegarder les findings
                for finding in parser.findings:
                    bh_finding = BloodHoundFinding(
                        analysis_id=analysis_obj.id,
                        category=finding['category'],
                        severity=finding['severity'],
                        title=finding['title'],
                        description=finding.get('description'),
                        affected_objects=finding.get('affected_objects'),
                        attack_path=finding.get('attack_path'),
                        recommendation=finding.get('recommendation'),
                        references=finding.get('references')
                    )
                    db.session.add(bh_finding)

                analysis_obj.status = 'completed'
                analysis_obj.completed_at = datetime.utcnow()
                db.session.commit()

            except Exception as e:
                analysis_obj = db.session.get(BloodHoundAnalysis, analysis.id)
                if analysis_obj:
                    analysis_obj.status = 'failed'
                    analysis_obj.error_message = str(e)
                    db.session.commit()

    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()

    return jsonify({
        'analysis': analysis.to_dict(),
        'files_uploaded': len(uploaded_files),
        'message': 'Analyse en cours...'
    }), 201


@ad_bp.route('/api/investigations/<int:inv_id>/bloodhound', methods=['GET'])
@login_required
def list_bloodhound_analyses(inv_id):
    """Lister les analyses BloodHound d'une investigation"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    analyses = BloodHoundAnalysis.query.filter_by(
        investigation_id=inv_id
    ).order_by(BloodHoundAnalysis.created_at.desc()).all()

    return jsonify([a.to_dict() for a in analyses])


@ad_bp.route('/api/bloodhound/<int:analysis_id>', methods=['GET'])
@login_required
def get_bloodhound_analysis(analysis_id):
    """Obtenir les details d'une analyse BloodHound"""
    analysis = BloodHoundAnalysis.query.get_or_404(analysis_id)
    investigation = Investigation.query.get(analysis.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    return jsonify(analysis.to_dict())


@ad_bp.route('/api/bloodhound/<int:analysis_id>/files', methods=['GET'])
@login_required
def get_bloodhound_files(analysis_id):
    """Obtenir les fichiers d'une analyse BloodHound"""
    analysis = BloodHoundAnalysis.query.get_or_404(analysis_id)
    investigation = Investigation.query.get(analysis.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    files = BloodHoundFile.query.filter_by(analysis_id=analysis_id).all()
    return jsonify([f.to_dict() for f in files])


@ad_bp.route('/api/bloodhound/<int:analysis_id>/findings', methods=['GET'])
@login_required
def get_bloodhound_findings(analysis_id):
    """Obtenir les findings d'une analyse BloodHound"""
    analysis = BloodHoundAnalysis.query.get_or_404(analysis_id)
    investigation = Investigation.query.get(analysis.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    # Filtres optionnels
    category = request.args.get('category')
    severity = request.args.get('severity')

    query = BloodHoundFinding.query.filter_by(analysis_id=analysis_id)

    if category:
        query = query.filter_by(category=category)
    if severity:
        query = query.filter_by(severity=severity)

    findings = query.order_by(
        db.case(
            (BloodHoundFinding.severity == 'critical', 1),
            (BloodHoundFinding.severity == 'high', 2),
            (BloodHoundFinding.severity == 'medium', 3),
            (BloodHoundFinding.severity == 'low', 4),
            else_=5
        )
    ).all()

    # Calculer le resume
    summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for f in BloodHoundFinding.query.filter_by(analysis_id=analysis_id).all():
        summary[f.severity] = summary.get(f.severity, 0) + 1

    return jsonify({
        'analysis': analysis.to_dict(),
        'summary': summary,
        'findings': [f.to_dict() for f in findings]
    })


@ad_bp.route('/api/bloodhound/<int:analysis_id>', methods=['DELETE'])
@login_required
def delete_bloodhound_analysis(analysis_id):
    """Supprimer une analyse BloodHound"""
    analysis = BloodHoundAnalysis.query.get_or_404(analysis_id)
    investigation = Investigation.query.get(analysis.investigation_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    # Supprimer les fichiers physiques
    analysis_folder = os.path.join(BLOODHOUND_UPLOAD_FOLDER, str(analysis_id))
    if os.path.exists(analysis_folder):
        import shutil
        shutil.rmtree(analysis_folder)

    # Supprimer en base (cascade supprimera files et findings)
    db.session.delete(analysis)
    db.session.commit()

    return jsonify({'message': 'Analyse supprimee'})


@ad_bp.route('/api/bloodhound/<int:analysis_id>/summary', methods=['GET'])
@login_required
def get_bloodhound_summary(analysis_id):
    """Obtenir un resume de l'analyse pour le dashboard"""
    analysis = BloodHoundAnalysis.query.get_or_404(analysis_id)
    investigation = Investigation.query.get(analysis.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    # Compter par categorie
    categories = db.session.query(
        BloodHoundFinding.category,
        db.func.count(BloodHoundFinding.id)
    ).filter_by(analysis_id=analysis_id).group_by(BloodHoundFinding.category).all()

    # Compter par severite
    severities = db.session.query(
        BloodHoundFinding.severity,
        db.func.count(BloodHoundFinding.id)
    ).filter_by(analysis_id=analysis_id).group_by(BloodHoundFinding.severity).all()

    return jsonify({
        'analysis': analysis.to_dict(),
        'by_category': {cat: count for cat, count in categories},
        'by_severity': {sev: count for sev, count in severities},
        'top_findings': [f.to_dict() for f in BloodHoundFinding.query.filter_by(
            analysis_id=analysis_id,
            severity='critical'
        ).limit(5).all()]
    })

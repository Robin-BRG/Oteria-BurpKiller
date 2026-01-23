# -*- coding: utf-8 -*-
"""
Module Active Directory - Enumeration LDAP, Kerberos, utilisateurs/groupes
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, ADScan, ADResult
from datetime import datetime
import threading
import socket
import struct
import base64
import hashlib
import time
import re

ad_bp = Blueprint('ad', __name__)


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
    # Cette fonction necessite impacket pour fonctionner correctement
    # Pour l'instant, on retourne une liste vide avec un message
    return [{
        'type': 'info',
        'name': 'RPC Enumeration',
        'value': 'Requires impacket library for full RPC enumeration',
        'severity': 'info'
    }]


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
    Scanner un controleur de domaine Active Directory

    Args:
        target: IP ou hostname du DC
        scan_type: 'basic' (ports + LDAP), 'full' (+ SMB + Kerberos checks)
        progress_callback: fonction(current, total) pour le suivi

    Returns:
        Liste de resultats
    """
    all_results = []
    steps = 4 if scan_type == 'full' else 2
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

    # Etape 2: Enumeration LDAP anonyme
    if progress_callback:
        progress_callback(current, steps)
    current += 1

    ldap_port = 389 if any(p['port'] == 389 for p in ports) else None
    if ldap_port:
        ldap_results = enumerate_ldap_anonymous(target, ldap_port)
        all_results.extend(ldap_results)

    if scan_type == 'full':
        # Etape 3: Verification SMB
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        if any(p['port'] == 445 for p in ports):
            smb_results = check_null_session(target)
            all_results.extend(smb_results)

        # Etape 4: Verification Kerberos
        if progress_callback:
            progress_callback(current, steps)
        current += 1

        if any(p['port'] == 88 for p in ports):
            krb_results = check_kerberos(target)
            all_results.extend(krb_results)

    if progress_callback:
        progress_callback(steps, steps)

    return all_results


def detect_dc(target):
    """Detecter si une cible est probablement un controleur de domaine"""
    dc_indicators = []
    score = 0

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

    return {
        'is_dc': is_dc,
        'confidence': min(score * 10, 100),
        'indicators': dc_indicators,
        'open_ports': ports
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

                # D'abord detecter si c'est un DC
                dc_detection = detect_dc(target)

                if dc_detection['is_dc']:
                    # C'est probablement un DC, on ajoute l'info
                    result = ADResult(
                        scan_id=scan_obj.id,
                        result_type='detection',
                        name='Domain Controller Detected',
                        value=f"Confidence: {dc_detection['confidence']}%",
                        severity='info',
                        description=f"Indicators: {', '.join(dc_detection['indicators'])}"
                    )
                    db.session.add(result)

                # Lancer le scan AD
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
                        description=r.get('description')
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

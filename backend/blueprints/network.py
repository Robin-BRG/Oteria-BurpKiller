# -*- coding: utf-8 -*-
"""
Module Network - Scan de ports, ping sweep, banner grabbing
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Investigation, NetworkScan, NetworkResult
from datetime import datetime
import threading
import socket
import struct
import time
import re

network_bp = Blueprint('network', __name__)


# ============================================================================
# SCANNER RESEAU
# ============================================================================

# Ports communs a scanner
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
    1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017
]

# Ports etendus
EXTENDED_PORTS = COMMON_PORTS + [
    20, 69, 79, 88, 102, 119, 123, 137, 138, 161, 162, 179, 194, 389, 464,
    500, 514, 515, 520, 521, 548, 554, 587, 631, 636, 873, 902, 989, 990,
    1080, 1194, 1723, 1883, 2049, 2082, 2083, 2181, 2222, 2375, 2376,
    3000, 3128, 3268, 3269, 3690, 4000, 4443, 4444, 5000, 5001, 5060,
    5222, 5269, 5353, 5357, 5672, 5984, 6000, 6066, 6379, 6443, 6660,
    6661, 6662, 6663, 6664, 6665, 6666, 6667, 6668, 6669, 7001, 7002,
    8000, 8008, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089,
    8090, 8181, 8222, 8333, 8400, 8500, 8834, 8888, 9000, 9001, 9042,
    9090, 9091, 9100, 9200, 9300, 9418, 9999, 10000, 10443, 11211,
    15672, 27018, 27019, 28017, 50000, 50070, 50090
]

# Services connus par port
PORT_SERVICES = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 110: 'POP3', 111: 'RPC', 135: 'MSRPC', 139: 'NetBIOS',
    143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 993: 'IMAPS', 995: 'POP3S',
    1433: 'MSSQL', 1521: 'Oracle', 3306: 'MySQL', 3389: 'RDP',
    5432: 'PostgreSQL', 5900: 'VNC', 6379: 'Redis', 8080: 'HTTP-Proxy',
    8443: 'HTTPS-Alt', 27017: 'MongoDB', 389: 'LDAP', 636: 'LDAPS',
    88: 'Kerberos', 464: 'Kerberos-Admin', 5985: 'WinRM-HTTP',
    5986: 'WinRM-HTTPS', 9389: 'AD-WS', 3268: 'LDAP-GC', 3269: 'LDAPS-GC'
}


def resolve_target(target):
    """Resoudre une cible (hostname ou IP) en IP"""
    try:
        # Si c'est deja une IP
        socket.inet_aton(target)
        return target
    except socket.error:
        # C'est un hostname, on resout
        try:
            return socket.gethostbyname(target)
        except socket.gaierror:
            return None


def scan_port(ip, port, timeout=2):
    """Scanner un port TCP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def grab_banner(ip, port, timeout=3):
    """Recuperer la banniere d'un service"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Envoyer une requete selon le service
        if port in [80, 8080, 8000, 8888]:
            sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
        elif port in [443, 8443]:
            sock.close()
            return "HTTPS (SSL/TLS)"
        elif port == 22:
            pass  # SSH envoie sa banniere automatiquement
        elif port == 21:
            pass  # FTP envoie sa banniere automatiquement
        elif port == 25:
            pass  # SMTP envoie sa banniere automatiquement
        else:
            sock.send(b'\r\n')

        banner = sock.recv(1024)
        sock.close()

        # Decoder et nettoyer
        try:
            banner_str = banner.decode('utf-8', errors='ignore').strip()
        except:
            banner_str = str(banner)

        # Limiter la taille
        if len(banner_str) > 500:
            banner_str = banner_str[:500] + '...'

        return banner_str if banner_str else None
    except Exception:
        return None


def ping_host(ip, timeout=2):
    """Verifier si un hote est accessible (TCP ping sur port 80 ou 443)"""
    # On utilise un TCP ping car ICMP necessite des privileges root
    for port in [80, 443, 22, 445]:
        if scan_port(ip, port, timeout):
            return True
    return False


def scan_network(target, scan_type='quick', progress_callback=None):
    """
    Scanner un reseau/hote

    Args:
        target: IP, hostname, ou range CIDR (ex: 192.168.1.0/24)
        scan_type: 'quick' (ports communs), 'full' (ports etendus), 'all' (1-65535)
        progress_callback: fonction(current, total) pour le suivi

    Returns:
        Liste de resultats
    """
    results = []

    # Determiner les ports a scanner
    if scan_type == 'quick':
        ports = COMMON_PORTS
    elif scan_type == 'full':
        ports = EXTENDED_PORTS
    elif scan_type == 'all':
        ports = list(range(1, 65536))
    else:
        ports = COMMON_PORTS

    # Resoudre la cible
    ip = resolve_target(target)
    if not ip:
        return []

    total = len(ports)
    current = 0

    # Scanner les ports
    for port in ports:
        current += 1
        if progress_callback:
            progress_callback(current, total)

        if scan_port(ip, port):
            # Port ouvert, recuperer la banniere
            banner = grab_banner(ip, port)
            service = PORT_SERVICES.get(port, 'Unknown')

            results.append({
                'ip': ip,
                'port': port,
                'state': 'open',
                'service': service,
                'banner': banner,
                'protocol': 'tcp'
            })

    return results


def ping_sweep(network, progress_callback=None):
    """
    Decouvrir les hotes actifs sur un reseau

    Args:
        network: Range CIDR (ex: 192.168.1.0/24) ou liste d'IPs
        progress_callback: fonction(current, total) pour le suivi

    Returns:
        Liste d'hotes actifs
    """
    hosts = []
    active_hosts = []

    # Parser le reseau CIDR
    if '/' in network:
        try:
            ip_parts = network.split('/')[0].split('.')
            prefix = int(network.split('/')[1])

            if prefix < 24:
                # Limiter a /24 pour eviter les scans trop longs
                prefix = 24

            # Generer les IPs
            num_hosts = 2 ** (32 - prefix)
            base_ip = struct.unpack('>I', socket.inet_aton('.'.join(ip_parts)))[0]

            for i in range(num_hosts):
                ip = socket.inet_ntoa(struct.pack('>I', base_ip + i))
                hosts.append(ip)
        except Exception:
            hosts = [network.split('/')[0]]
    else:
        hosts = [network]

    total = len(hosts)
    current = 0

    for ip in hosts:
        current += 1
        if progress_callback:
            progress_callback(current, total)

        if ping_host(ip):
            # Essayer de resoudre le hostname
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = None

            active_hosts.append({
                'ip': ip,
                'hostname': hostname,
                'status': 'up'
            })

    return active_hosts


# ============================================================================
# ROUTES API
# ============================================================================

@network_bp.route('/api/investigations/<int:inv_id>/network-scans', methods=['POST'])
@login_required
def start_network_scan(inv_id):
    """Lancer un scan reseau"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_edit(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    data = request.get_json() or {}
    target = data.get('target', '')
    scan_type = data.get('scan_type', 'quick')  # quick, full, all
    scan_mode = data.get('scan_mode', 'portscan')  # portscan, pingsweep

    if not target:
        # Extraire l'hote de l'URL cible de l'investigation
        from urllib.parse import urlparse
        parsed = urlparse(investigation.target_url)
        target = parsed.hostname or parsed.netloc

    if not target:
        return jsonify({'error': 'Cible non specifiee'}), 400

    # Creer le scan
    scan = NetworkScan(
        investigation_id=inv_id,
        started_by_id=current_user.id,
        target=target,
        scan_type=scan_type,
        scan_mode=scan_mode,
        status='running'
    )
    db.session.add(scan)
    db.session.commit()

    # Lancer le scan en arriere-plan
    def run_scan():
        from app import app
        with app.app_context():
            try:
                scan_obj = db.session.get(NetworkScan, scan.id)

                def progress_callback(current, total):
                    scan_obj.progress_current = current
                    scan_obj.progress_total = total
                    db.session.commit()

                if scan_mode == 'pingsweep':
                    results = ping_sweep(target, progress_callback)
                else:
                    results = scan_network(target, scan_type, progress_callback)

                # Sauvegarder les resultats
                for r in results:
                    result = NetworkResult(
                        scan_id=scan_obj.id,
                        ip=r.get('ip', ''),
                        port=r.get('port'),
                        state=r.get('state', r.get('status', '')),
                        service=r.get('service', ''),
                        banner=r.get('banner'),
                        hostname=r.get('hostname'),
                        protocol=r.get('protocol', 'tcp')
                    )
                    db.session.add(result)

                scan_obj.status = 'completed'
                scan_obj.completed_at = datetime.utcnow()
                db.session.commit()

            except Exception as e:
                scan_obj = db.session.get(NetworkScan, scan.id)
                if scan_obj:
                    scan_obj.status = 'failed'
                    scan_obj.error_message = str(e)
                    db.session.commit()

    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

    return jsonify(scan.to_dict()), 201


@network_bp.route('/api/investigations/<int:inv_id>/network-scans', methods=['GET'])
@login_required
def list_network_scans(inv_id):
    """Lister les scans reseau d'une investigation"""
    investigation = Investigation.query.get_or_404(inv_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    scans = NetworkScan.query.filter_by(investigation_id=inv_id).order_by(NetworkScan.created_at.desc()).all()
    return jsonify([s.to_dict() for s in scans])


@network_bp.route('/api/network-scans/<int:scan_id>', methods=['GET'])
@login_required
def get_network_scan(scan_id):
    """Obtenir le statut d'un scan reseau"""
    scan = NetworkScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    return jsonify(scan.to_dict())


@network_bp.route('/api/network-scans/<int:scan_id>/results', methods=['GET'])
@login_required
def get_network_results(scan_id):
    """Obtenir les resultats d'un scan reseau"""
    scan = NetworkScan.query.get_or_404(scan_id)
    investigation = Investigation.query.get(scan.investigation_id)

    if not investigation.user_can_view(current_user):
        return jsonify({'error': 'Non autorise'}), 403

    results = NetworkResult.query.filter_by(scan_id=scan_id).all()
    return jsonify({
        'scan': scan.to_dict(),
        'results': [r.to_dict() for r in results]
    })

# -*- coding: utf-8 -*-
"""
Module de génération de rapports - Format HTML et PDF
"""
from datetime import datetime
from jinja2 import Template
import os


def generate_html_report(investigation, user):
    """
    Génère un rapport HTML pour une investigation

    Args:
        investigation: Objet Investigation avec toutes les données
        user: Utilisateur qui génère le rapport

    Returns:
        str: Contenu HTML du rapport
    """

    # Collecter toutes les données
    report_data = {
        'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'generated_by': user.username,
        'investigation': {
            'id': investigation.id,
            'name': investigation.name,
            'target_url': investigation.target_url,
            'description': investigation.description,
            'created_at': investigation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'owner': investigation.owner.username
        },
        'summary': {
            'total_scans': 0,
            'total_vulnerabilities': 0,
            'total_network_hosts': 0,
            'total_ad_results': 0,
            'critical_vulns': 0,
            'high_vulns': 0,
            'medium_vulns': 0,
            'low_vulns': 0
        },
        'recon_results': [],
        'enum_results': [],
        'network_results': [],
        'ad_results': [],
        'vulnerabilities': [],
        'js_secrets': [],
        'http_requests': []
    }

    # Reconnaissance
    recon_scans = investigation.scans.all()
    report_data['summary']['total_scans'] += len(recon_scans)

    for scan in recon_scans:
        results = scan.results.all()
        for result in results:
            report_data['recon_results'].append({
                'path': result.path,
                'status_code': result.status_code,
                'content_length': result.content_length,
                'response_time': result.response_time
            })

    # Enumération
    enum_scans = investigation.enum_scans.all()
    for scan in enum_scans:
        results = scan.results.all()
        for result in results:
            report_data['enum_results'].append({
                'result_type': result.result_type,
                'name': result.name,
                'value': result.value,
                'severity': result.severity
            })

    # Scans réseau
    network_scans = investigation.network_scans.all()
    for scan in network_scans:
        results = scan.results.all()
        for result in results:
            report_data['network_results'].append({
                'ip': result.ip,
                'port': result.port,
                'state': result.state,
                'service': result.service,
                'banner': result.banner,
                'hostname': result.hostname
            })
            if result.state == 'open' or result.status == 'up':
                report_data['summary']['total_network_hosts'] += 1

    # Scans Active Directory
    ad_scans = investigation.ad_scans.all()
    for scan in ad_scans:
        results = scan.results.all()
        for result in results:
            report_data['ad_results'].append({
                'result_type': result.result_type,
                'name': result.name,
                'value': result.value,
                'severity': result.severity,
                'port': result.port,
                'service': result.service,
                'description': result.description
            })
            report_data['summary']['total_ad_results'] += 1

    # Vulnérabilités
    vuln_scans = investigation.vuln_scans.all()
    for scan in vuln_scans:
        vulns = scan.vulnerabilities.all()
        for vuln in vulns:
            report_data['vulnerabilities'].append({
                'vuln_type': vuln.vuln_type,
                'severity': vuln.severity,
                'url': vuln.url,
                'parameter': vuln.parameter,
                'method': vuln.method,
                'payload': vuln.payload,
                'evidence': vuln.evidence,
                'description': vuln.description,
                'recommendation': vuln.recommendation
            })
            report_data['summary']['total_vulnerabilities'] += 1

            # Compter par sévérité
            if vuln.severity == 'critical':
                report_data['summary']['critical_vulns'] += 1
            elif vuln.severity == 'high':
                report_data['summary']['high_vulns'] += 1
            elif vuln.severity == 'medium':
                report_data['summary']['medium_vulns'] += 1
            else:
                report_data['summary']['low_vulns'] += 1

    # Secrets JavaScript
    js_secrets = investigation.js_secrets.all()
    for secret in js_secrets:
        report_data['js_secrets'].append({
            'secret_type': secret.secret_type,
            'severity': secret.severity,
            'source_url': secret.source_url,
            'secret_preview': secret.secret_preview,
            'description': secret.description
        })

    # Requêtes HTTP (dernières 20)
    http_requests = investigation.http_requests.order_by('created_at').limit(20).all()
    for req in http_requests:
        report_data['http_requests'].append({
            'method': req.method,
            'url': req.url,
            'response_status': req.response_status,
            'response_time': req.response_time
        })

    # Template HTML
    html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport - {{ investigation.name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header {
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #2c3e50;
            font-size: 32px;
            margin-bottom: 10px;
        }

        .header .meta {
            color: #7f8c8d;
            font-size: 14px;
        }

        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }

        .section h3 {
            color: #34495e;
            font-size: 18px;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .info-item {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
        }

        .info-item strong {
            color: #2c3e50;
            display: block;
            margin-bottom: 5px;
        }

        .summary-cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }

        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .summary-card.critical {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .summary-card.high {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }

        .summary-card.medium {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }

        .summary-card.low {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }

        .summary-card .number {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .summary-card .label {
            font-size: 14px;
            opacity: 0.9;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }

        table th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        table td {
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }

        table tr:hover {
            background: #f8f9fa;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge.critical {
            background: #e74c3c;
            color: white;
        }

        .badge.high {
            background: #e67e22;
            color: white;
        }

        .badge.medium {
            background: #f39c12;
            color: white;
        }

        .badge.low {
            background: #3498db;
            color: white;
        }

        .badge.info {
            background: #95a5a6;
            color: white;
        }

        .badge.success {
            background: #27ae60;
            color: white;
        }

        .badge.warning {
            background: #f39c12;
            color: white;
        }

        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }

        code {
            background: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #95a5a6;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Rapport de Pentest</h1>
            <div class="meta">
                Investigation: <strong>{{ investigation.name }}</strong><br>
                Généré le: {{ generated_at }} par {{ generated_by }}
            </div>
        </div>

        <!-- Informations générales -->
        <div class="section">
            <h2>Informations générales</h2>
            <div class="info-grid">
                <div class="info-item">
                    <strong>Cible</strong>
                    {{ investigation.target_url }}
                </div>
                <div class="info-item">
                    <strong>Date de création</strong>
                    {{ investigation.created_at }}
                </div>
                <div class="info-item">
                    <strong>Propriétaire</strong>
                    {{ investigation.owner }}
                </div>
                <div class="info-item">
                    <strong>ID Investigation</strong>
                    #{{ investigation.id }}
                </div>
            </div>
            {% if investigation.description %}
            <div class="info-item" style="margin-top: 15px;">
                <strong>Description</strong>
                {{ investigation.description }}
            </div>
            {% endif %}
        </div>

        <!-- Résumé exécutif -->
        <div class="section">
            <h2>Résumé exécutif</h2>
            <div class="summary-cards">
                <div class="summary-card critical">
                    <div class="number">{{ summary.critical_vulns }}</div>
                    <div class="label">Critiques</div>
                </div>
                <div class="summary-card high">
                    <div class="number">{{ summary.high_vulns }}</div>
                    <div class="label">Hautes</div>
                </div>
                <div class="summary-card medium">
                    <div class="number">{{ summary.medium_vulns }}</div>
                    <div class="label">Moyennes</div>
                </div>
                <div class="summary-card low">
                    <div class="number">{{ summary.low_vulns }}</div>
                    <div class="label">Basses</div>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <strong>Total scans</strong>
                    {{ summary.total_scans }}
                </div>
                <div class="info-item">
                    <strong>Vulnérabilités détectées</strong>
                    {{ summary.total_vulnerabilities }}
                </div>
                <div class="info-item">
                    <strong>Hôtes réseau découverts</strong>
                    {{ summary.total_network_hosts }}
                </div>
                <div class="info-item">
                    <strong>Résultats AD</strong>
                    {{ summary.total_ad_results }}
                </div>
            </div>
        </div>

        <!-- Vulnérabilités -->
        {% if vulnerabilities %}
        <div class="section">
            <h2>Vulnérabilités détectées</h2>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>URL</th>
                        <th>Paramètre</th>
                        <th>Sévérité</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {% for vuln in vulnerabilities %}
                    <tr>
                        <td><strong>{{ vuln.vuln_type }}</strong></td>
                        <td><code>{{ vuln.url }}</code></td>
                        <td>{{ vuln.parameter or '-' }}</td>
                        <td><span class="badge {{ vuln.severity }}">{{ vuln.severity }}</span></td>
                        <td>{{ vuln.description or '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Secrets JavaScript -->
        {% if js_secrets %}
        <div class="section">
            <h2>Secrets JavaScript exposés</h2>
            <table>
                <thead>
                    <tr>
                        <th>Type de secret</th>
                        <th>URL source</th>
                        <th>Aperçu</th>
                        <th>Sévérité</th>
                    </tr>
                </thead>
                <tbody>
                    {% for secret in js_secrets %}
                    <tr>
                        <td><strong>{{ secret.secret_type }}</strong></td>
                        <td><code>{{ secret.source_url }}</code></td>
                        <td><code>{{ secret.secret_preview }}</code></td>
                        <td><span class="badge {{ secret.severity }}">{{ secret.severity }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Résultats réseau -->
        {% if network_results %}
        <div class="section">
            <h2>Scan réseau</h2>
            <h3>Ports ouverts détectés</h3>
            <table>
                <thead>
                    <tr>
                        <th>IP</th>
                        <th>Port</th>
                        <th>Service</th>
                        <th>État</th>
                        <th>Banner</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in network_results %}
                    <tr>
                        <td><code>{{ result.ip }}</code></td>
                        <td><strong>{{ result.port }}</strong></td>
                        <td>{{ result.service or '-' }}</td>
                        <td><span class="badge success">{{ result.state }}</span></td>
                        <td><small>{{ result.banner or '-' }}</small></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Résultats Active Directory -->
        {% if ad_results %}
        <div class="section">
            <h2>Énumération Active Directory</h2>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Nom</th>
                        <th>Valeur</th>
                        <th>Sévérité</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in ad_results %}
                    <tr>
                        <td><strong>{{ result.result_type }}</strong></td>
                        <td>{{ result.name }}</td>
                        <td><code>{{ result.value }}</code></td>
                        <td><span class="badge {{ result.severity }}">{{ result.severity }}</span></td>
                        <td>{{ result.description or '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Reconnaissance web -->
        {% if recon_results %}
        <div class="section">
            <h2>Reconnaissance web</h2>
            <h3>Chemins découverts ({{ recon_results|length }} résultats)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Chemin</th>
                        <th>Status</th>
                        <th>Taille</th>
                        <th>Temps (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in recon_results[:50] %}
                    <tr>
                        <td><code>{{ result.path }}</code></td>
                        <td><span class="badge {% if result.status_code >= 200 and result.status_code < 300 %}success{% elif result.status_code >= 400 %}warning{% else %}info{% endif %}">{{ result.status_code }}</span></td>
                        <td>{{ result.content_length or '-' }} bytes</td>
                        <td>{{ result.response_time or '-' }}</td>
                    </tr>
                    {% endfor %}
                    {% if recon_results|length > 50 %}
                    <tr>
                        <td colspan="4" class="empty-state">
                            ... et {{ recon_results|length - 50 }} autres résultats
                        </td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Énumération technologies -->
        {% if enum_results %}
        <div class="section">
            <h2>Technologies détectées</h2>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Nom</th>
                        <th>Valeur</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in enum_results %}
                    <tr>
                        <td><strong>{{ result.result_type }}</strong></td>
                        <td>{{ result.name }}</td>
                        <td><code>{{ result.value }}</code></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Footer -->
        <div class="footer">
            Rapport généré par <strong>Oteria BurpKiller</strong> - Framework de pentest modulaire<br>
            Python pour la Cyber - M1 2025-2026
        </div>
    </div>
</body>
</html>
    """

    # Rendre le template
    template = Template(html_template)
    html_content = template.render(**report_data)

    return html_content


def generate_pdf_report(investigation, user):
    """
    Génère un rapport PDF pour une investigation

    Args:
        investigation: Objet Investigation
        user: Utilisateur qui génère le rapport

    Returns:
        bytes: Contenu binaire du PDF
    """
    from weasyprint import HTML

    # Générer le HTML
    html_content = generate_html_report(investigation, user)

    # Convertir en PDF
    pdf = HTML(string=html_content).write_pdf()

    return pdf

"""
name: Technology & Headers Analyzer
description: Detecte les technologies utilisees et analyse les headers HTTP de securite
category: Enumeration
"""
import requests
import re
from urllib.parse import urlparse

# Headers de securite a verifier
SECURITY_HEADERS = {
    'Strict-Transport-Security': {
        'description': 'Force HTTPS pour toutes les requetes futures',
        'missing': 'insecure',
        'recommendation': 'Ajouter: Strict-Transport-Security: max-age=31536000; includeSubDomains'
    },
    'X-Frame-Options': {
        'description': 'Protege contre le clickjacking',
        'missing': 'warning',
        'recommendation': 'Ajouter: X-Frame-Options: DENY ou SAMEORIGIN'
    },
    'X-Content-Type-Options': {
        'description': 'Empeche le MIME sniffing',
        'missing': 'warning',
        'recommendation': 'Ajouter: X-Content-Type-Options: nosniff'
    },
    'Content-Security-Policy': {
        'description': 'Protege contre XSS et injection de contenu',
        'missing': 'warning',
        'recommendation': 'Configurer une CSP adaptee a votre application'
    },
    'X-XSS-Protection': {
        'description': 'Active la protection XSS du navigateur',
        'missing': 'warning',
        'recommendation': 'Ajouter: X-XSS-Protection: 1; mode=block'
    },
    'Referrer-Policy': {
        'description': 'Controle les informations de referrer envoyees',
        'missing': 'info',
        'recommendation': 'Ajouter: Referrer-Policy: strict-origin-when-cross-origin'
    },
    'Permissions-Policy': {
        'description': 'Controle les fonctionnalites du navigateur',
        'missing': 'info',
        'recommendation': 'Configurer selon les besoins de votre application'
    }
}

# Patterns de detection de technologies
TECH_PATTERNS = {
    'server': {
        'nginx': {'pattern': r'nginx(?:/([0-9.]+))?', 'category': 'Web Server'},
        'apache': {'pattern': r'Apache(?:/([0-9.]+))?', 'category': 'Web Server'},
        'iis': {'pattern': r'Microsoft-IIS(?:/([0-9.]+))?', 'category': 'Web Server'},
        'cloudflare': {'pattern': r'cloudflare', 'category': 'CDN'},
    },
    'x-powered-by': {
        'php': {'pattern': r'PHP(?:/([0-9.]+))?', 'category': 'Backend'},
        'express': {'pattern': r'Express', 'category': 'Backend Framework'},
        'asp.net': {'pattern': r'ASP\.NET', 'category': 'Backend Framework'},
    },
    'html': {
        'react': {'pattern': r'__REACT', 'category': 'Frontend Framework'},
        'vue': {'pattern': r'__VUE__|Vue\.js', 'category': 'Frontend Framework'},
        'angular': {'pattern': r'ng-version|angular', 'category': 'Frontend Framework'},
        'wordpress': {'pattern': r'wp-content|wordpress', 'category': 'CMS'},
        'drupal': {'pattern': r'drupal', 'category': 'CMS'},
        'joomla': {'pattern': r'joomla', 'category': 'CMS'},
        'django': {'pattern': r'csrfmiddlewaretoken', 'category': 'Backend Framework'},
        'flask': {'pattern': r'flask', 'category': 'Backend Framework'},
        'laravel': {'pattern': r'laravel', 'category': 'Backend Framework'},
        'nextjs': {'pattern': r'__NEXT', 'category': 'Frontend Framework'},
        'gatsby': {'pattern': r'gatsby', 'category': 'Frontend Framework'},
    },
    'cookies': {
        'php': {'pattern': r'PHPSESSID', 'category': 'Backend'},
        'asp.net': {'pattern': r'ASP\.NET_SessionId', 'category': 'Backend Framework'},
        'django': {'pattern': r'sessionid|csrftoken', 'category': 'Backend Framework'},
        'laravel': {'pattern': r'laravel_session', 'category': 'Backend Framework'},
    }
}


def analyze_headers(target_url):
    """Analyse les headers HTTP et detecte les technologies"""
    results = []

    try:
        response = requests.get(
            target_url,
            timeout=10,
            verify=False,
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )

        # Analyser les headers de securite
        for header_name, info in SECURITY_HEADERS.items():
            header_value = response.headers.get(header_name)

            if header_value:
                # Header present
                security_level = 'secure'
                description = f"{info['description']}. Valeur: {header_value}"

                # Analyser la valeur pour certains headers
                if header_name == 'X-Frame-Options' and header_value.upper() == 'ALLOW-FROM':
                    security_level = 'warning'
                    description += ". Attention: ALLOW-FROM est deprecie"

            else:
                # Header manquant
                security_level = info['missing']
                description = f"{info['description']}. {info['recommendation']}"

            results.append({
                'type': 'header',
                'category': 'Security',
                'name': header_name,
                'value': header_value,
                'confidence': 'high',
                'security_level': security_level,
                'description': description
            })

        # Detecter technologies via headers
        for header_name, techs in TECH_PATTERNS.items():
            if header_name in ['server', 'x-powered-by']:
                header_value = response.headers.get(header_name.replace('_', '-').title())
                if header_value:
                    for tech_name, tech_info in techs.items():
                        match = re.search(tech_info['pattern'], header_value, re.IGNORECASE)
                        if match:
                            version = match.group(1) if match.groups() else None
                            results.append({
                                'type': 'technology',
                                'category': tech_info['category'],
                                'name': tech_name.title(),
                                'value': version,
                                'confidence': 'high',
                                'security_level': None,
                                'description': f"Detecte via header {header_name}"
                            })

        # Analyser le HTML
        html_content = response.text[:50000]  # Limiter a 50KB
        for tech_name, tech_info in TECH_PATTERNS['html'].items():
            if re.search(tech_info['pattern'], html_content, re.IGNORECASE):
                results.append({
                    'type': 'technology',
                    'category': tech_info['category'],
                    'name': tech_name.title(),
                    'value': None,
                    'confidence': 'medium',
                    'security_level': None,
                    'description': 'Detecte dans le code HTML'
                })

        # Analyser les cookies
        cookies = response.cookies
        for cookie_name in cookies.keys():
            for tech_name, tech_info in TECH_PATTERNS['cookies'].items():
                if re.search(tech_info['pattern'], cookie_name, re.IGNORECASE):
                    results.append({
                        'type': 'technology',
                        'category': tech_info['category'],
                        'name': tech_name.title(),
                        'value': None,
                        'confidence': 'high',
                        'security_level': None,
                        'description': f"Detecte via cookie: {cookie_name}"
                    })

        # Ajouter headers informatifs
        info_headers = ['Server', 'X-Powered-By', 'Content-Type', 'Set-Cookie']
        for header in info_headers:
            value = response.headers.get(header)
            if value and header not in ['Server', 'X-Powered-By']:  # Deja traites
                results.append({
                    'type': 'header',
                    'category': 'Information',
                    'name': header,
                    'value': value[:200],  # Limiter la longueur
                    'confidence': 'high',
                    'security_level': None,
                    'description': 'Header informatif'
                })

    except requests.exceptions.RequestException as e:
        results.append({
            'type': 'error',
            'category': 'Error',
            'name': 'Erreur de connexion',
            'value': str(e),
            'confidence': 'high',
            'security_level': 'insecure',
            'description': f"Impossible de se connecter a {target_url}"
        })

    return results


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tech_detector.py <url>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"[*] Analyzing {target}...")
    results = analyze_headers(target)

    print(f"\n[+] Found {len(results)} results:")
    for r in results:
        print(f"  [{r['type']}] {r['name']}: {r['value'] or 'N/A'}")

# -*- coding: utf-8 -*-
"""
Scanner JavaScript pour detecter les secrets
API keys, tokens, endpoints, credentials, etc.
"""
import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup


# Patterns de secrets connus
SECRET_PATTERNS = {
    'google_api': {
        'pattern': r'AIza[0-9A-Za-z\-_]{35}',
        'severity': 'critical',
        'description': 'Google API Key exposée'
    },
    'aws_access_key': {
        'pattern': r'AKIA[0-9A-Z]{16}',
        'severity': 'critical',
        'description': 'AWS Access Key ID exposée'
    },
    'aws_secret_key': {
        'pattern': r'aws_secret_access_key\s*=\s*[\'"]?([A-Za-z0-9/+=]{40})[\'"]?',
        'severity': 'critical',
        'description': 'AWS Secret Access Key exposée'
    },
    'stripe_key': {
        'pattern': r'sk_live_[0-9a-zA-Z]{24,}',
        'severity': 'critical',
        'description': 'Stripe Live Secret Key exposée'
    },
    'github_token': {
        'pattern': r'gh[pousr]_[A-Za-z0-9_]{36,}',
        'severity': 'critical',
        'description': 'GitHub Token exposé'
    },
    'slack_token': {
        'pattern': r'xox[baprs]-[0-9]{10,12}-[0-9]{10,12}-[a-zA-Z0-9]{24,}',
        'severity': 'high',
        'description': 'Slack Token exposé'
    },
    'jwt_token': {
        'pattern': r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
        'severity': 'high',
        'description': 'JWT Token exposé'
    },
    'bearer_token': {
        'pattern': r'Bearer\s+[A-Za-z0-9\-._~+/]+',
        'severity': 'high',
        'description': 'Bearer Token exposé'
    },
    'api_key_generic': {
        'pattern': r'[\'"]?api[_-]?key[\'"]?\s*[:=]\s*[\'"]([A-Za-z0-9_\-]{20,})[\'"]',
        'severity': 'medium',
        'description': 'API Key générique détectée'
    },
    'password_generic': {
        'pattern': r'[\'"]?password[\'"]?\s*[:=]\s*[\'"]([^\'\"]{8,})[\'"]',
        'severity': 'medium',
        'description': 'Password en clair détecté'
    },
    'private_key': {
        'pattern': r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
        'severity': 'critical',
        'description': 'Private Key exposée'
    },
}

# Patterns pour endpoints API
ENDPOINT_PATTERNS = [
    r'[\'"`](https?://[^\'"` ]+)[\'"`]',  # URLs completes
    r'[\'"`](/api/[^\'"` ]+)[\'"`]',  # API endpoints
    r'[\'"`](/v[0-9]+/[^\'"` ]+)[\'"`]',  # Versioned endpoints
]


def find_js_files(base_url, timeout=10):
    """Trouve tous les fichiers JS d'une page"""
    js_files = []

    try:
        response = requests.get(base_url, timeout=timeout, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Scripts inline
        for script in soup.find_all('script', src=True):
            js_url = urljoin(base_url, script['src'])
            js_files.append(js_url)

    except Exception as e:
        print(f"Erreur lors de la recherche de fichiers JS: {e}")

    return js_files


def scan_js_file(js_url, timeout=10):
    """Scan un fichier JS pour detecter des secrets"""
    secrets_found = []

    try:
        response = requests.get(js_url, timeout=timeout, verify=False)
        js_content = response.text

        # Chercher chaque pattern de secret
        for secret_type, config in SECRET_PATTERNS.items():
            matches = re.finditer(config['pattern'], js_content, re.IGNORECASE)

            for match in matches:
                secret_value = match.group(0)

                # Masquer partiellement le secret pour l'affichage
                if len(secret_value) > 10:
                    secret_preview = secret_value[:5] + '...' + secret_value[-5:]
                else:
                    secret_preview = secret_value[:3] + '...'

                # Extraire le contexte (ligne de code)
                context = extract_context_around_match(js_content, match)

                secrets_found.append({
                    'secret_type': secret_type,
                    'severity': config['severity'],
                    'source_url': js_url,
                    'secret_value': secret_value,
                    'secret_preview': secret_preview,
                    'context': context,
                    'description': config['description']
                })

        # Chercher des endpoints cachés
        endpoints = find_hidden_endpoints(js_content)
        for endpoint in endpoints:
            secrets_found.append({
                'secret_type': 'hidden_endpoint',
                'severity': 'low',
                'source_url': js_url,
                'secret_value': endpoint,
                'secret_preview': endpoint,
                'context': f'Endpoint: {endpoint}',
                'description': f'Endpoint caché trouvé dans le JavaScript'
            })

    except Exception as e:
        print(f"Erreur lors du scan de {js_url}: {e}")

    return secrets_found


def extract_context_around_match(content, match, context_lines=2):
    """Extrait quelques lignes autour d'un match"""
    try:
        # Trouver la ligne du match
        lines = content[:match.start()].split('\n')
        line_num = len(lines)

        # Extraire les lignes autour
        all_lines = content.split('\n')
        start_line = max(0, line_num - context_lines)
        end_line = min(len(all_lines), line_num + context_lines + 1)

        context_lines_text = all_lines[start_line:end_line]
        return '\n'.join(context_lines_text).strip()
    except:
        return match.group(0)


def is_public_endpoint(endpoint):
    """Verifie si un endpoint est un domaine public connu (faux positif)"""
    endpoint_lower = endpoint.lower()

    # Domaines publics à ignorer
    ignored_domains = [
        # Standards/CDN
        'w3.org', 'schema.org', 'xmlns.com',
        'gstatic.com', 'googleapis.com', 'googleusercontent.com',
        'cloudflare.com', 'akamai.net', 'fastly.net',

        # Social/Analytics
        'google-analytics.com', 'googletagmanager.com',
        'facebook.com', 'twitter.com', 'linkedin.com',
        'doubleclick.net', 'google.com/ads',

        # Fonts/Assets
        'fonts.googleapis.com', 'fonts.gstatic.com',
        'youtube.com/watch', 'youtu.be', 'ytimg.com',
        'i.ytimg.com', 's.ytimg.com',

        # Images/CDN publics
        'imgur.com', 'cloudinary.com', 'imgix.net',

        # Libraries
        'jquery.com', 'jsdelivr.net', 'unpkg.com', 'cdnjs.com'
    ]

    # URLs standards non intéressantes
    ignored_patterns = [
        'http://www.w3.org/',
        'https://www.w3.org/',
        '/img/', '/images/', '/static/', '/assets/',
        '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp',
        '.css', '.woff', '.ttf', '.json'
    ]

    # Vérifier domaines ignorés
    for domain in ignored_domains:
        if domain in endpoint_lower:
            return True

    # Vérifier patterns ignorés
    for pattern in ignored_patterns:
        if pattern in endpoint_lower:
            return True

    return False


def find_hidden_endpoints(js_content):
    """Trouve des endpoints API cachés dans le JS"""
    endpoints = set()

    for pattern in ENDPOINT_PATTERNS:
        matches = re.finditer(pattern, js_content)
        for match in matches:
            endpoint = match.group(1)

            # Filtrer les endpoints publics
            if not is_public_endpoint(endpoint):
                # Ne garder que les endpoints qui ressemblent à des APIs internes
                if any(api_marker in endpoint.lower() for api_marker in ['/api/', '/v1/', '/v2/', '/graphql', '/rest/']):
                    endpoints.add(endpoint)

    return list(endpoints)[:10]  # Limiter à 10 endpoints pertinents


def scan_js_secrets(base_url, progress_callback=None):
    """
    Scan principal pour detecter les secrets dans les JS
    """
    all_secrets = []

    # Trouver tous les fichiers JS
    js_files = find_js_files(base_url)

    if progress_callback:
        progress_callback(0, len(js_files))

    # Scanner chaque fichier JS
    for i, js_url in enumerate(js_files):
        if progress_callback:
            progress_callback(i + 1, len(js_files))

        secrets = scan_js_file(js_url)
        all_secrets.extend(secrets)

    return all_secrets

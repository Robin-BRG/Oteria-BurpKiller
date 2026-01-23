"""
name: HTTP Path Scanner
description: Scanner HTTP pour la decouverte de chemins et repertoires
category: Reconnaissance
"""
import requests
import time
import sys

# Wordlist de base pour la decouverte
COMMON_PATHS = [
    '/', 'admin', 'api', 'login', 'register', 'logout', 'dashboard',
    'static', 'assets', 'images', 'img', 'css', 'js', 'scripts',
    'docs', 'documentation', 'help', 'about', 'contact',
    'user', 'users', 'profile', 'account', 'settings',
    'config', 'configuration', 'backup', 'backups',
    'upload', 'uploads', 'files', 'download', 'downloads',
    'test', 'tests', 'dev', 'debug', 'staging',
    'wp-admin', 'wp-content', 'wp-includes',
    'phpmyadmin', 'pma', 'mysql', 'database',
    '.git', '.env', '.htaccess', 'robots.txt', 'sitemap.xml',
    'api/v1', 'api/v2', 'api/users', 'api/admin', 'api/health', 'api/status',
    'graphql', 'rest', 'swagger', 'api-docs',
    'admin/login', 'admin/dashboard', 'admin/users',
    'auth', 'auth/login', 'oauth', 'oauth/token',
    'search', 'blog', 'news', 'articles',
    'products', 'shop', 'cart', 'checkout',
    'terms', 'privacy', 'legal', 'faq'
]

AGGRESSIVE_PATHS = [
    '.git/config', '.git/HEAD', '.svn', '.hg',
    '.env.local', '.env.production', '.env.development',
    'config.php', 'config.json', 'config.yaml', 'config.yml',
    'database.sql', 'dump.sql', 'backup.sql',
    'composer.json', 'package.json', 'requirements.txt',
    'Dockerfile', 'docker-compose.yml',
    '.aws/credentials', '.ssh/id_rsa',
    'server-status', 'server-info',
    'phpinfo.php', 'info.php', 'test.php',
    'console', 'shell', 'cmd', 'terminal',
    'cgi-bin', 'scripts', 'bin',
    'tmp', 'temp', 'cache', 'logs', 'log',
    'error_log', 'access_log', 'debug.log',
    'readme.md', 'README.md', 'CHANGELOG.md',
    'license.txt', 'LICENSE', 'version.txt'
]

def scan_http(target_url, mode='normal', wordlist='common', progress_callback=None):
    """Scanner HTTP pour decouvrir les paths"""
    target_url = target_url.rstrip('/')

    # Determiner les paths a tester
    paths_to_test = COMMON_PATHS.copy()
    if mode == 'aggressive':
        paths_to_test.extend(AGGRESSIVE_PATHS)

    # Determiner le delai
    if mode == 'stealth':
        delay = 1.0
    elif mode == 'aggressive':
        delay = 0.05
    else:
        delay = 0.2

    # Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive'
    }

    results = []
    total_paths = len(paths_to_test)

    for index, path in enumerate(paths_to_test, 1):
        if path.startswith('/'):
            full_url = target_url + path
        else:
            full_url = target_url + '/' + path
        
        try:
            response = requests.get(
                full_url,
                headers=headers,
                timeout=10,
                allow_redirects=False,
                verify=False
            )
            
            if response.status_code != 404:
                content_type = response.headers.get('Content-Type', '')
                if ';' in content_type:
                    content_type = content_type.split(';')[0].strip()
                
                results.append({
                    'path': path if path.startswith('/') else '/' + path,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'content_type': content_type or None
                })
                
                print(f"[+] {response.status_code} {full_url}")

            time.sleep(delay)

        except requests.exceptions.RequestException:
            pass

        # Report progress
        if progress_callback:
            progress_callback(index, total_paths)

    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python http_scanner.py <url> [mode]")
        print("Modes: stealth, normal, aggressive")
        sys.exit(1)
    
    target = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'normal'
    
    print(f"[*] Scanning {target} in {mode} mode...")
    results = scan_http(target, mode)
    print(f"\n[*] Found {len(results)} paths")

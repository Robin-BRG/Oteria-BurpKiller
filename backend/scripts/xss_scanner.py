# -*- coding: utf-8 -*-
"""
Scanner XSS (Cross-Site Scripting)
Teste differentes payloads XSS sur les endpoints
"""
import requests
from urllib.parse import urlparse, parse_qs, urlencode
import re


# Payloads XSS classiques
XSS_PAYLOADS = [
    # Basic XSS
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<body onload=alert(1)>",
    "<iframe src=javascript:alert(1)>",

    # Event handlers
    "' onmouseover='alert(1)",
    "\" onmouseover=\"alert(1)",
    "<input onfocus=alert(1) autofocus>",
    "<select onfocus=alert(1) autofocus>",
    "<textarea onfocus=alert(1) autofocus>",

    # Encoded
    "&#60;script&#62;alert(1)&#60;/script&#62;",
    "%3Cscript%3Ealert(1)%3C/script%3E",

    # Filter bypass
    "<ScRiPt>alert(1)</sCrIpT>",
    "<script>alert(String.fromCharCode(88,83,83))</script>",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",

    # DOM-based
    "#<img src=x onerror=alert(1)>",

    # Polyglot
    "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//\\x3e",
]

# Marqueur unique pour detecter les reflections
UNIQUE_MARKER = "XSS_TEST_MARKER_12345"

# Patterns pour detecter XSS
XSS_PATTERNS = [
    r"<script[^>]*>.*alert\(.*\).*</script>",
    r"onerror\s*=\s*['\"]?alert\(",
    r"onload\s*=\s*['\"]?alert\(",
    r"onmouseover\s*=\s*['\"]?alert\(",
    r"javascript:\s*alert\(",
]


def test_xss_on_url(url, method='GET', timeout=10):
    """
    Test XSS sur une URL
    Returns: list de vulnerabilites trouvees
    """
    vulnerabilities = []

    parsed_url = urlparse(url)

    # Tester GET parameters
    if parsed_url.query:
        params = parse_qs(parsed_url.query)
        for param_name in params.keys():
            vulns = test_parameter_xss(url, param_name, method='GET', timeout=timeout)
            vulnerabilities.extend(vulns)

    return vulnerabilities


def test_parameter_xss(url, param_name, method='GET', timeout=10):
    """Test un parametre specifique avec differents payloads XSS"""
    vulnerabilities = []

    # Test 1: Marqueur unique pour voir s'il est reflété
    marker_found = False
    try:
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        params[param_name] = [UNIQUE_MARKER]
        test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(params, doseq=True)}"

        response = requests.get(test_url, timeout=timeout, verify=False)
        if UNIQUE_MARKER in response.text:
            marker_found = True
    except:
        return vulnerabilities

    # Si le marqueur n'est pas reflété, pas besoin de tester les payloads
    if not marker_found:
        return vulnerabilities

    # Tester chaque payload XSS
    for payload in XSS_PAYLOADS:
        try:
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            params[param_name] = [payload]

            test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{urlencode(params, doseq=True)}"

            response = requests.get(test_url, timeout=timeout, verify=False)

            # Verifier si le payload est présent dans la reponse (reflected)
            if payload in response.text or is_xss_reflected(payload, response.text):
                # Extraire le contexte
                context = extract_reflection_context(response.text, payload)

                vulnerabilities.append({
                    'vuln_type': 'xss',
                    'severity': 'high',
                    'url': url,
                    'parameter': param_name,
                    'method': method,
                    'payload': payload,
                    'evidence': context,
                    'description': f'XSS Reflected detectee sur le parametre "{param_name}". Le payload est reflété dans la reponse sans sanitization.',
                    'recommendation': 'Encoder toutes les donnees utilisateur avant affichage (HTML entities). Utiliser Content-Security-Policy headers.'
                })
                break  # Une detection suffit

        except Exception as e:
            continue

    return vulnerabilities


def is_xss_reflected(payload, response_text):
    """Verifie si un payload XSS est present dans la reponse"""
    for pattern in XSS_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE | re.DOTALL):
            return True
    return False


def extract_reflection_context(text, payload, context_length=150):
    """Extrait le contexte autour d'un payload reflété"""
    try:
        index = text.find(payload)
        if index != -1:
            start = max(0, index - context_length // 2)
            end = min(len(text), index + len(payload) + context_length // 2)
            return text[start:end].strip()
    except:
        pass
    return "Payload refléte dans la reponse"


def scan_xss_on_endpoints(endpoints, progress_callback=None):
    """
    Scan XSS sur une liste d'endpoints
    endpoints: list de dicts avec 'url' et optionnellement 'method'
    progress_callback: fonction appelée pour mettre à jour la progression
    """
    all_vulnerabilities = []
    total = len(endpoints)

    for i, endpoint in enumerate(endpoints):
        url = endpoint.get('url')
        method = endpoint.get('method', 'GET')

        if progress_callback:
            progress_callback(i + 1, total)

        vulns = test_xss_on_url(url, method=method)
        all_vulnerabilities.extend(vulns)

    return all_vulnerabilities

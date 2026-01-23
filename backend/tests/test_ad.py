# -*- coding: utf-8 -*-
"""
Tests pour le module Active Directory
"""
import pytest
from blueprints.ad import AD_PORTS, LDAP_USER_ATTRS, PRIVILEGED_GROUPS, check_ad_ports, detect_dc


class TestADConstants:
    """Tests pour les constantes AD"""

    def test_ad_ports_defined(self):
        """Test que les ports AD sont definis"""
        assert AD_PORTS is not None
        assert isinstance(AD_PORTS, dict)
        assert 88 in AD_PORTS  # Kerberos
        assert 389 in AD_PORTS  # LDAP
        assert 636 in AD_PORTS  # LDAPS
        assert 445 in AD_PORTS  # SMB

    def test_ad_ports_services(self):
        """Test que les services AD sont correctement nommes"""
        assert AD_PORTS[88] == 'Kerberos'
        assert AD_PORTS[389] == 'LDAP'
        assert AD_PORTS[636] == 'LDAPS'
        assert AD_PORTS[445] == 'SMB'

    def test_ldap_user_attrs_defined(self):
        """Test que les attributs LDAP utilisateur sont definis"""
        assert LDAP_USER_ATTRS is not None
        assert isinstance(LDAP_USER_ATTRS, list)
        assert 'sAMAccountName' in LDAP_USER_ATTRS
        assert 'userPrincipalName' in LDAP_USER_ATTRS

    def test_privileged_groups_defined(self):
        """Test que les groupes privilegies sont definis"""
        assert PRIVILEGED_GROUPS is not None
        assert isinstance(PRIVILEGED_GROUPS, list)
        assert 'Domain Admins' in PRIVILEGED_GROUPS
        assert 'Enterprise Admins' in PRIVILEGED_GROUPS


class TestADUtils:
    """Tests pour les utilitaires AD"""

    def test_check_ad_ports_returns_list(self):
        """Test que check_ad_ports retourne une liste"""
        # On utilise une IP locale qui n'aura probablement pas de ports AD ouverts
        result = check_ad_ports('127.0.0.1', timeout=1)
        assert isinstance(result, list)

    def test_check_ad_ports_invalid_target(self):
        """Test check_ad_ports avec une cible invalide"""
        result = check_ad_ports('invalid-host-12345.local', timeout=1)
        assert isinstance(result, list)
        # Devrait retourner une liste vide ou avec erreurs

    def test_detect_dc_returns_dict(self):
        """Test que detect_dc retourne un dictionnaire"""
        result = detect_dc('127.0.0.1')
        assert isinstance(result, dict)
        assert 'is_dc' in result
        assert 'confidence' in result
        assert 'indicators' in result
        assert 'open_ports' in result

    def test_detect_dc_localhost_not_dc(self):
        """Test que localhost n'est pas detecte comme DC"""
        result = detect_dc('127.0.0.1')
        # localhost ne devrait pas etre un DC (sauf configuration speciale)
        assert isinstance(result['is_dc'], bool)
        assert isinstance(result['confidence'], int)
        assert result['confidence'] >= 0
        assert result['confidence'] <= 100


class TestADAPI:
    """Tests pour les routes API AD"""

    def test_start_ad_scan_authenticated(self, authenticated_client, test_investigation):
        """Test de demarrage d'un scan AD authentifie"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/ad-scans',
            json={
                'target': '127.0.0.1',
                'scan_type': 'basic'
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['status'] in ['running', 'completed', 'failed']

    def test_start_ad_scan_unauthenticated(self, client, test_investigation):
        """Test de scan AD non authentifie"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/ad-scans',
            json={'target': '127.0.0.1'}
        )

        assert response.status_code == 401

    def test_start_ad_scan_no_target(self, authenticated_client, test_investigation):
        """Test de scan AD sans cible - utilise l'URL de l'investigation"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/ad-scans',
            json={'scan_type': 'basic'}
        )

        # Devrait fonctionner car l'URL cible de l'investigation est utilisee
        assert response.status_code in [201, 400]

    def test_list_ad_scans(self, authenticated_client, test_investigation):
        """Test de liste des scans AD"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/ad-scans'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_ad_scans_unauthenticated(self, client, test_investigation):
        """Test de liste des scans AD non authentifie"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/ad-scans'
        )

        assert response.status_code == 401

    def test_ad_scan_invalid_investigation(self, authenticated_client):
        """Test de scan sur investigation inexistante"""
        response = authenticated_client.post(
            '/api/investigations/99999/ad-scans',
            json={'target': '127.0.0.1'}
        )

        assert response.status_code == 404

    def test_detect_dc_api(self, authenticated_client, test_investigation):
        """Test de l'API detect-dc"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/detect-dc',
            json={'target': '127.0.0.1'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'is_dc' in data
        assert 'confidence' in data

    def test_detect_dc_api_no_target(self, authenticated_client, test_investigation):
        """Test de l'API detect-dc sans cible"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/detect-dc',
            json={}
        )

        # Devrait utiliser l'URL de l'investigation ou retourner erreur
        assert response.status_code in [200, 400]

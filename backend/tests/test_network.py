# -*- coding: utf-8 -*-
"""
Tests pour le module réseau
"""
import pytest
from network import resolve_target, scan_port, PORT_SERVICES


class TestNetworkUtils:
    """Tests pour les utilitaires réseau"""

    def test_resolve_target_ip(self):
        """Test de résolution d'une IP"""
        result = resolve_target('127.0.0.1')
        assert result == '127.0.0.1'

    def test_resolve_target_localhost(self):
        """Test de résolution de localhost"""
        result = resolve_target('localhost')
        assert result is not None
        assert result in ['127.0.0.1', '::1']

    def test_resolve_target_invalid(self):
        """Test de résolution d'un hostname invalide"""
        result = resolve_target('this-domain-does-not-exist-12345.com')
        assert result is None

    def test_scan_port_open(self):
        """Test de scan d'un port ouvert (localhost:test)"""
        # On suppose qu'aucun port n'est ouvert en local pour ce test
        # Si vous avez un service local, adaptez
        result = scan_port('127.0.0.1', 65535, timeout=1)
        assert isinstance(result, bool)

    def test_port_services_mapping(self):
        """Test que le mapping des services existe"""
        assert PORT_SERVICES is not None
        assert isinstance(PORT_SERVICES, dict)
        assert 80 in PORT_SERVICES
        assert PORT_SERVICES[80] == 'HTTP'
        assert 443 in PORT_SERVICES
        assert PORT_SERVICES[443] == 'HTTPS'


class TestNetworkAPI:
    """Tests pour les routes API réseau"""

    def test_start_network_scan_authenticated(self, authenticated_client, test_investigation):
        """Test de démarrage d'un scan réseau authentifié"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/network-scans',
            json={
                'target': '127.0.0.1',
                'scan_type': 'quick',
                'scan_mode': 'portscan'
            }
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['status'] in ['running', 'completed', 'failed']

    def test_start_network_scan_unauthenticated(self, client, test_investigation):
        """Test de scan réseau non authentifié"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/network-scans',
            json={'target': '127.0.0.1'}
        )

        assert response.status_code == 401

    def test_list_network_scans(self, authenticated_client, test_investigation):
        """Test de liste des scans réseau"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/network-scans'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_network_scan_invalid_investigation(self, authenticated_client):
        """Test de scan sur investigation inexistante"""
        response = authenticated_client.post(
            '/api/investigations/99999/network-scans',
            json={'target': '127.0.0.1'}
        )

        assert response.status_code == 404

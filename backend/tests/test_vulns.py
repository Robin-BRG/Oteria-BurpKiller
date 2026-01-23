# -*- coding: utf-8 -*-
"""
Tests pour le module de scan de vulnerabilites
"""
import pytest


class TestVulnsAPI:
    """Tests pour les routes API de vulnerabilites"""

    def test_start_vuln_scan_authenticated(self, authenticated_client, test_investigation):
        """Test de demarrage d'un scan de vulns authentifie"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/vuln-scan',
            json={'scan_type': 'all'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['status'] in ['running', 'completed', 'failed']

    def test_start_vuln_scan_sqli_only(self, authenticated_client, test_investigation):
        """Test de scan SQLi uniquement"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/vuln-scan',
            json={'scan_type': 'sqli'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['scan_type'] == 'sqli'

    def test_start_vuln_scan_xss_only(self, authenticated_client, test_investigation):
        """Test de scan XSS uniquement"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/vuln-scan',
            json={'scan_type': 'xss'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['scan_type'] == 'xss'

    def test_start_vuln_scan_unauthenticated(self, client, test_investigation):
        """Test de scan non authentifie"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/vuln-scan',
            json={'scan_type': 'all'}
        )

        assert response.status_code == 401

    def test_list_vuln_scans(self, authenticated_client, test_investigation):
        """Test de liste des scans de vulnerabilites"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/vuln-scans'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_vuln_scans_unauthenticated(self, client, test_investigation):
        """Test de liste des scans non authentifie"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/vuln-scans'
        )

        assert response.status_code == 401

    def test_vuln_scan_invalid_investigation(self, authenticated_client):
        """Test de scan sur investigation inexistante"""
        response = authenticated_client.post(
            '/api/investigations/99999/vuln-scan',
            json={'scan_type': 'all'}
        )

        assert response.status_code == 404

    def test_start_js_scan(self, authenticated_client, test_investigation):
        """Test de demarrage d'un scan JavaScript"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/js-scan',
            json={}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'started'

    def test_start_js_scan_unauthenticated(self, client, test_investigation):
        """Test de scan JS non authentifie"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/js-scan',
            json={}
        )

        assert response.status_code == 401

    def test_get_js_secrets(self, authenticated_client, test_investigation):
        """Test de recuperation des secrets JS"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/js-secrets'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_js_secrets_unauthenticated(self, client, test_investigation):
        """Test de recuperation des secrets JS non authentifie"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/js-secrets'
        )

        assert response.status_code == 401

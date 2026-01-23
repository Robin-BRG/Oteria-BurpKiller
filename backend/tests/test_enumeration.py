# -*- coding: utf-8 -*-
"""
Tests pour le module d'enumeration des technologies
"""
import pytest


class TestEnumerationAPI:
    """Tests pour les routes API d'enumeration"""

    def test_start_enum_scan_authenticated(self, authenticated_client, test_investigation):
        """Test de demarrage d'un scan d'enumeration authentifie"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/enum',
            json={}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['status'] in ['running', 'completed', 'failed']

    def test_start_enum_scan_unauthenticated(self, client, test_investigation):
        """Test de scan d'enumeration non authentifie"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/enum',
            json={}
        )

        assert response.status_code == 401

    def test_list_enum_scans(self, authenticated_client, test_investigation):
        """Test de liste des scans d'enumeration"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/enum'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_enum_scans_unauthenticated(self, client, test_investigation):
        """Test de liste non authentifie"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/enum'
        )

        assert response.status_code == 401

    def test_enum_scan_invalid_investigation(self, authenticated_client):
        """Test de scan sur investigation inexistante"""
        response = authenticated_client.post(
            '/api/investigations/99999/enum',
            json={}
        )

        assert response.status_code == 404

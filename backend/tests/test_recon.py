# -*- coding: utf-8 -*-
"""
Tests pour le module de reconnaissance HTTP
"""
import pytest
from blueprints.recon import get_parent_path, COMMON_PATHS, AGGRESSIVE_PATHS


class TestReconUtils:
    """Tests pour les utilitaires de reconnaissance"""

    def test_common_paths_defined(self):
        """Test que les paths communs sont definis"""
        assert COMMON_PATHS is not None
        assert isinstance(COMMON_PATHS, list)
        assert len(COMMON_PATHS) > 0
        assert '/' in COMMON_PATHS or 'admin' in COMMON_PATHS

    def test_aggressive_paths_defined(self):
        """Test que les paths agressifs sont definis"""
        assert AGGRESSIVE_PATHS is not None
        assert isinstance(AGGRESSIVE_PATHS, list)
        assert len(AGGRESSIVE_PATHS) > 0

    def test_get_parent_path_root(self):
        """Test de get_parent_path pour la racine"""
        assert get_parent_path('/') is None

    def test_get_parent_path_simple(self):
        """Test de get_parent_path pour un chemin simple"""
        assert get_parent_path('/admin') == '/'

    def test_get_parent_path_nested(self):
        """Test de get_parent_path pour un chemin imbrique"""
        assert get_parent_path('/api/users') == '/api'

    def test_get_parent_path_deep(self):
        """Test de get_parent_path pour un chemin profond"""
        assert get_parent_path('/api/v1/users/list') == '/api/v1/users'


class TestReconAPI:
    """Tests pour les routes API de reconnaissance"""

    def test_start_scan_authenticated(self, authenticated_client, test_investigation):
        """Test de demarrage d'un scan authentifie"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/scans',
            json={'scan_mode': 'normal'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['status'] in ['running', 'completed', 'failed']

    def test_start_scan_aggressive(self, authenticated_client, test_investigation):
        """Test de scan en mode agressif"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/scans',
            json={'scan_mode': 'aggressive'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['scan_mode'] == 'aggressive'

    def test_start_scan_stealth(self, authenticated_client, test_investigation):
        """Test de scan en mode stealth"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/scans',
            json={'scan_mode': 'stealth'}
        )

        assert response.status_code == 201

    def test_start_scan_unauthenticated(self, client, test_investigation):
        """Test de scan non authentifie"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/scans',
            json={'scan_mode': 'normal'}
        )

        assert response.status_code == 401

    def test_list_scans(self, authenticated_client, test_investigation):
        """Test de liste des scans"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/scans'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_scans_unauthenticated(self, client, test_investigation):
        """Test de liste non authentifie"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/scans'
        )

        assert response.status_code == 401

    def test_scan_invalid_investigation(self, authenticated_client):
        """Test de scan sur investigation inexistante"""
        response = authenticated_client.post(
            '/api/investigations/99999/scans',
            json={'scan_mode': 'normal'}
        )

        assert response.status_code == 404

    def test_start_scan_default_mode(self, authenticated_client, test_investigation):
        """Test de scan avec mode par defaut"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/scans',
            json={}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['scan_mode'] == 'normal'  # Mode par defaut

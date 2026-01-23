# -*- coding: utf-8 -*-
"""
Tests pour le module HTTP Tools (Request Builder)
"""
import pytest


class TestHttpToolsAPI:
    """Tests pour les routes API HTTP Tools"""

    def test_send_http_request_get(self, authenticated_client, test_investigation):
        """Test d'envoi d'une requete GET"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/http-requests',
            json={
                'method': 'GET',
                'url': 'https://httpbin.org/get',
                'headers': {'User-Agent': 'Test'}
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
        assert data['method'] == 'GET'
        assert data['url'] == 'https://httpbin.org/get'

    def test_send_http_request_post(self, authenticated_client, test_investigation):
        """Test d'envoi d'une requete POST"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/http-requests',
            json={
                'method': 'POST',
                'url': 'https://httpbin.org/post',
                'headers': {'Content-Type': 'application/json'},
                'body': '{"test": "data"}'
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['method'] == 'POST'

    def test_send_http_request_missing_method(self, authenticated_client, test_investigation):
        """Test d'envoi sans methode"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/http-requests',
            json={
                'url': 'https://example.com'
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_send_http_request_missing_url(self, authenticated_client, test_investigation):
        """Test d'envoi sans URL"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/http-requests',
            json={
                'method': 'GET'
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_send_http_request_unauthenticated(self, client, test_investigation):
        """Test d'envoi non authentifie"""
        response = client.post(
            f'/api/investigations/{test_investigation.id}/http-requests',
            json={
                'method': 'GET',
                'url': 'https://example.com'
            }
        )

        assert response.status_code == 401

    def test_list_http_requests(self, authenticated_client, test_investigation):
        """Test de liste des requetes HTTP"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/http-requests'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_http_requests_unauthenticated(self, client, test_investigation):
        """Test de liste non authentifie"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/http-requests'
        )

        assert response.status_code == 401

    def test_http_request_invalid_investigation(self, authenticated_client):
        """Test sur investigation inexistante"""
        response = authenticated_client.post(
            '/api/investigations/99999/http-requests',
            json={
                'method': 'GET',
                'url': 'https://example.com'
            }
        )

        assert response.status_code == 404

    def test_send_request_with_custom_headers(self, authenticated_client, test_investigation):
        """Test avec headers personnalises"""
        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/http-requests',
            json={
                'method': 'GET',
                'url': 'https://httpbin.org/headers',
                'headers': {
                    'X-Custom-Header': 'test-value',
                    'Authorization': 'Bearer test-token'
                }
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['headers']['X-Custom-Header'] == 'test-value'

# -*- coding: utf-8 -*-
"""
Tests pour le module Terminal
"""
import pytest


class TestTerminalAPI:
    """Tests pour les routes API Terminal"""

    def test_execute_simple_code(self, authenticated_client):
        """Test d'execution de code Python simple"""
        response = authenticated_client.post(
            '/api/terminal/execute',
            json={
                'code': 'print("Hello World")',
                'timeout': 5
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'stdout' in data
        assert 'stderr' in data
        assert 'returncode' in data
        assert 'Hello World' in data['stdout']
        assert data['returncode'] == 0

    def test_execute_with_error(self, authenticated_client):
        """Test d'execution de code avec erreur"""
        response = authenticated_client.post(
            '/api/terminal/execute',
            json={
                'code': 'print(undefined_variable)',
                'timeout': 5
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['returncode'] != 0
        assert 'NameError' in data['stderr']

    def test_execute_math_operation(self, authenticated_client):
        """Test d'execution d'operation mathematique"""
        response = authenticated_client.post(
            '/api/terminal/execute',
            json={
                'code': 'result = 2 + 2\nprint(f"Result: {result}")',
                'timeout': 5
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'Result: 4' in data['stdout']
        assert data['returncode'] == 0

    def test_execute_unauthenticated(self, client):
        """Test d'execution non authentifiee"""
        response = client.post(
            '/api/terminal/execute',
            json={
                'code': 'print("test")',
                'timeout': 5
            }
        )

        assert response.status_code == 401

    def test_execute_empty_code(self, authenticated_client):
        """Test d'execution de code vide"""
        response = authenticated_client.post(
            '/api/terminal/execute',
            json={
                'code': '',
                'timeout': 5
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['returncode'] == 0

    def test_execute_with_loop(self, authenticated_client):
        """Test d'execution avec boucle"""
        response = authenticated_client.post(
            '/api/terminal/execute',
            json={
                'code': 'for i in range(3):\n    print(i)',
                'timeout': 5
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert '0' in data['stdout']
        assert '1' in data['stdout']
        assert '2' in data['stdout']

    def test_get_history(self, authenticated_client):
        """Test de recuperation de l'historique"""
        response = authenticated_client.get('/api/terminal/history')

        assert response.status_code == 200
        data = response.get_json()
        assert 'history' in data
        assert isinstance(data['history'], list)

    def test_get_history_unauthenticated(self, client):
        """Test d'historique non authentifie"""
        response = client.get('/api/terminal/history')

        assert response.status_code == 401

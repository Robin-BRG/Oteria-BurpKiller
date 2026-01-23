# -*- coding: utf-8 -*-
"""
Tests pour le module Presence
"""
import pytest
from blueprints.presence import start_process, stop_process, get_active_users_count, get_running_processes_count


class TestPresenceFunctions:
    """Tests pour les fonctions utilitaires de presence"""

    def test_start_process(self, app):
        """Test de demarrage d'un processus"""
        pid = start_process('test', 'Test process', owner='testuser')

        assert pid is not None
        assert isinstance(pid, str)
        assert len(pid) > 0

    def test_stop_process(self, app):
        """Test d'arret d'un processus"""
        pid = start_process('test', 'Test process to stop', owner='testuser')
        result = stop_process(pid, status='completed')

        assert result is True

    def test_stop_nonexistent_process(self, app):
        """Test d'arret d'un processus inexistant"""
        result = stop_process('nonexistent-pid-12345', status='stopped')

        assert result is False

    def test_stop_process_with_message(self, app):
        """Test d'arret avec message"""
        pid = start_process('test', 'Test process', owner='testuser')
        result = stop_process(pid, status='failed', message='Test error message')

        assert result is True

    def test_get_active_users_count(self, app):
        """Test du compteur d'utilisateurs actifs"""
        count = get_active_users_count()

        assert isinstance(count, int)
        assert count >= 0

    def test_get_running_processes_count(self, app):
        """Test du compteur de processus en cours"""
        count = get_running_processes_count()

        assert isinstance(count, int)
        assert count >= 0


class TestPresenceAPI:
    """Tests pour les routes API Presence"""

    def test_heartbeat(self, client):
        """Test du heartbeat"""
        response = client.post(
            '/api/presence/heartbeat',
            json={'page': 'test-page'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'

    def test_heartbeat_authenticated(self, authenticated_client):
        """Test du heartbeat authentifie"""
        response = authenticated_client.post(
            '/api/presence/heartbeat',
            json={'page': 'investigation/1'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'

    def test_get_active_users(self, client):
        """Test de recuperation des utilisateurs actifs"""
        response = client.get('/api/presence/active')

        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert isinstance(data['users'], list)

    def test_get_processes(self, client):
        """Test de recuperation des processus"""
        response = client.get('/api/processes')

        assert response.status_code == 200
        data = response.get_json()
        assert 'processes' in data
        assert isinstance(data['processes'], list)

    def test_get_stats(self, client):
        """Test de recuperation des statistiques"""
        response = client.get('/api/presence/stats')

        assert response.status_code == 200
        data = response.get_json()
        assert 'active_users' in data
        assert 'running_processes' in data
        assert isinstance(data['active_users'], int)
        assert isinstance(data['running_processes'], int)

    def test_heartbeat_creates_user(self, client):
        """Test que le heartbeat cree un utilisateur"""
        # Envoyer un heartbeat
        client.post(
            '/api/presence/heartbeat',
            json={
                'page': 'test-page',
                'username': 'heartbeat-test-user'
            }
        )

        # Verifier que l'utilisateur apparait
        response = client.get('/api/presence/active')
        data = response.get_json()

        usernames = [u['username'] for u in data['users']]
        assert 'heartbeat-test-user' in usernames

# -*- coding: utf-8 -*-
"""
Tests pour le module d'authentification
"""
import pytest
from models import User


class TestAuthentication:
    """Tests pour l'authentification"""

    def test_register_success(self, client):
        """Test d'inscription réussie"""
        response = client.post('/api/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['username'] == 'newuser'
        assert data['email'] == 'new@example.com'

    def test_register_duplicate_username(self, client, test_user):
        """Test d'inscription avec username existant"""
        response = client.post('/api/register', json={
            'username': test_user.username,
            'email': 'another@example.com',
            'password': 'Password123!'
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_register_duplicate_email(self, client, test_user):
        """Test d'inscription avec email existant"""
        response = client.post('/api/register', json={
            'username': 'anotheruser',
            'email': test_user.email,
            'password': 'Password123!'
        })

        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        """Test d'inscription avec champs manquants"""
        response = client.post('/api/register', json={
            'username': 'user'
        })

        assert response.status_code == 400

    def test_login_success(self, client, test_user):
        """Test de connexion réussie"""
        response = client.post('/api/login', json={
            'username': test_user.username,
            'password': 'password123'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == test_user.username

    def test_login_wrong_password(self, client, test_user):
        """Test de connexion avec mauvais mot de passe"""
        response = client.post('/api/login', json={
            'username': test_user.username,
            'password': 'wrongpassword'
        })

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test de connexion avec utilisateur inexistant"""
        response = client.post('/api/login', json={
            'username': 'nonexistent',
            'password': 'password'
        })

        assert response.status_code == 401

    def test_logout(self, authenticated_client):
        """Test de déconnexion"""
        response = authenticated_client.post('/api/logout')
        assert response.status_code == 200

    def test_check_auth_authenticated(self, authenticated_client):
        """Test de vérification d'auth pour utilisateur connecté"""
        response = authenticated_client.get('/api/check-auth')
        assert response.status_code == 200

    def test_check_auth_not_authenticated(self, client):
        """Test de vérification d'auth pour utilisateur non connecté"""
        response = client.get('/api/check-auth')
        assert response.status_code == 401

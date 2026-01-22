# -*- coding: utf-8 -*-
"""
Tests pour le module investigations
"""
import pytest


class TestInvestigationAPI:
    """Tests pour les routes API des investigations"""

    def test_list_investigations_authenticated(self, authenticated_client, test_investigation):
        """Test de liste des investigations"""
        response = authenticated_client.get('/api/investigations')

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_investigations_unauthenticated(self, client):
        """Test de liste des investigations non authentifié"""
        response = client.get('/api/investigations')

        assert response.status_code == 401

    def test_get_investigation_detail(self, authenticated_client, test_investigation):
        """Test de récupération des détails d'une investigation"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == test_investigation.id
        assert data['name'] == test_investigation.name

    def test_create_investigation(self, authenticated_client):
        """Test de création d'investigation"""
        response = authenticated_client.post('/api/investigations', json={
            'name': 'New Investigation',
            'target_url': 'https://newtest.com',
            'description': 'New test description'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'New Investigation'
        assert data['target_url'] == 'https://newtest.com'

    def test_create_investigation_missing_fields(self, authenticated_client):
        """Test de création d'investigation avec champs manquants"""
        response = authenticated_client.post('/api/investigations', json={
            'name': 'Incomplete Investigation'
        })

        assert response.status_code == 400

    def test_update_investigation(self, authenticated_client, test_investigation):
        """Test de modification d'investigation"""
        response = authenticated_client.put(
            f'/api/investigations/{test_investigation.id}',
            json={
                'name': 'Updated Name',
                'description': 'Updated description'
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Name'
        assert data['description'] == 'Updated description'

    def test_delete_investigation(self, authenticated_client, app, test_user):
        """Test de suppression d'investigation"""
        from models import db, Investigation

        # Créer une investigation à supprimer
        inv_to_delete = Investigation(
            name='To Delete',
            target_url='https://delete.com',
            owner_id=test_user.id
        )
        db.session.add(inv_to_delete)
        db.session.commit()
        inv_id = inv_to_delete.id

        response = authenticated_client.delete(f'/api/investigations/{inv_id}')

        assert response.status_code == 200

        # Vérifier que l'investigation n'existe plus
        deleted_inv = Investigation.query.get(inv_id)
        assert deleted_inv is None

    def test_cannot_edit_others_investigation(self, app, client, test_investigation):
        """Test qu'on ne peut pas éditer l'investigation d'un autre"""
        from models import db, User

        # Créer un autre utilisateur
        other_user = User(username='other', email='other@test.com')
        other_user.password_hash = 'hash'
        db.session.add(other_user)
        db.session.commit()

        # Se connecter en tant qu'autre user
        with client.session_transaction() as sess:
            sess['_user_id'] = str(other_user.id)

        response = client.put(
            f'/api/investigations/{test_investigation.id}',
            json={'name': 'Hacked Name'}
        )

        assert response.status_code == 403


class TestInvestigationMembers:
    """Tests pour la gestion des membres d'investigation"""

    def test_add_member_to_investigation(self, app, authenticated_client, test_investigation):
        """Test d'ajout de membre à une investigation"""
        from models import db, User

        # Créer un nouveau user à ajouter
        new_member = User(username='newmember', email='newmember@test.com')
        new_member.password_hash = 'hash'
        db.session.add(new_member)
        db.session.commit()

        response = authenticated_client.post(
            f'/api/investigations/{test_investigation.id}/members',
            json={
                'username': 'newmember',
                'role': 'viewer'
            }
        )

        assert response.status_code in [200, 201]

    def test_list_investigation_members(self, authenticated_client, test_investigation):
        """Test de liste des membres"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/members'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_cannot_add_member_to_others_investigation(self, app, client, test_investigation):
        """Test qu'on ne peut pas ajouter un membre à l'investigation d'un autre"""
        from models import db, User

        other_user = User(username='attacker', email='attacker@test.com')
        other_user.password_hash = 'hash'
        db.session.add(other_user)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(other_user.id)

        response = client.post(
            f'/api/investigations/{test_investigation.id}/members',
            json={'username': 'somebodyelse', 'role': 'admin'}
        )

        assert response.status_code == 403

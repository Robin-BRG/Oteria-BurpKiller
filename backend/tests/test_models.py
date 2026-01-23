# -*- coding: utf-8 -*-
"""
Tests pour les modèles de base de données
"""
import pytest
from models import User, Investigation, InvestigationMember, ReconScan, NetworkScan, ADScan


class TestUserModel:
    """Tests pour le modèle User"""

    def test_create_user(self, app):
        """Test de création d'utilisateur"""
        user = User(username='testuser', email='test@test.com')
        user.password_hash = 'hashed_password'

        from models import db
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'

    def test_user_to_dict(self, test_user):
        """Test de sérialisation utilisateur"""
        user_dict = test_user.to_dict()

        assert user_dict['id'] == test_user.id
        assert user_dict['username'] == test_user.username
        assert user_dict['email'] == test_user.email
        assert 'password_hash' not in user_dict


class TestInvestigationModel:
    """Tests pour le modèle Investigation"""

    def test_create_investigation(self, app, test_user):
        """Test de création d'investigation"""
        from models import db

        inv = Investigation(
            name='Test Inv',
            target_url='https://test.com',
            owner_id=test_user.id
        )
        db.session.add(inv)
        db.session.commit()

        assert inv.id is not None
        assert inv.name == 'Test Inv'
        assert inv.owner_id == test_user.id

    def test_investigation_to_dict(self, test_investigation):
        """Test de sérialisation investigation"""
        inv_dict = test_investigation.to_dict()

        assert inv_dict['id'] == test_investigation.id
        assert inv_dict['name'] == test_investigation.name
        assert inv_dict['target_url'] == test_investigation.target_url

    def test_user_can_view_owner(self, test_investigation, test_user):
        """Test que le propriétaire peut voir"""
        assert test_investigation.user_can_view(test_user) is True

    def test_user_can_edit_owner(self, test_investigation, test_user):
        """Test que le propriétaire peut éditer"""
        assert test_investigation.user_can_edit(test_user) is True

    def test_user_cannot_view_private(self, app, test_investigation):
        """Test qu'un autre user ne peut pas voir une inv privée"""
        from models import db
        other_user = User(username='other', email='other@test.com')
        other_user.password_hash = 'hash'
        db.session.add(other_user)
        db.session.commit()

        assert test_investigation.user_can_view(other_user) is False

    def test_user_can_view_public(self, app, test_user):
        """Test qu'un user peut voir une inv publique"""
        from models import db

        public_inv = Investigation(
            name='Public Inv',
            target_url='https://test.com',
            owner_id=test_user.id,
            is_public=True
        )
        db.session.add(public_inv)
        db.session.commit()

        other_user = User(username='other', email='other@test.com')
        other_user.password_hash = 'hash'
        db.session.add(other_user)
        db.session.commit()

        assert public_inv.user_can_view(other_user) is True


class TestRelationships:
    """Tests pour les relations entre modèles"""

    def test_investigation_owner_relationship(self, test_investigation, test_user):
        """Test de la relation investigation -> owner"""
        assert test_investigation.owner.id == test_user.id
        assert test_investigation.owner.username == test_user.username

    def test_user_investigations_relationship(self, test_user, test_investigation):
        """Test de la relation user -> investigations"""
        investigations = test_user.owned_investigations.all()
        assert len(investigations) >= 1
        assert test_investigation in investigations

    def test_add_member_to_investigation(self, app, test_investigation):
        """Test d'ajout de membre à une investigation"""
        from models import db

        new_user = User(username='member', email='member@test.com')
        new_user.password_hash = 'hash'
        db.session.add(new_user)
        db.session.commit()

        membership = InvestigationMember(
            investigation_id=test_investigation.id,
            user_id=new_user.id,
            role='viewer'
        )
        db.session.add(membership)
        db.session.commit()

        assert len(test_investigation.members.all()) == 1
        assert test_investigation.members.first().user_id == new_user.id

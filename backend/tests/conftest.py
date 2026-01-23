# -*- coding: utf-8 -*-
"""
Configuration pytest - Fixtures partagées pour tous les tests
"""
import pytest
from app import app as flask_app
from models import db, User, Investigation


@pytest.fixture
def app():
    """Fixture Flask app pour les tests"""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Fixture client de test"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Fixture CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Créer un utilisateur de test"""
    from auth import bcrypt

    user = User(
        username='testuser',
        email='test@example.com'
    )
    user.password_hash = bcrypt.generate_password_hash('password123').decode('utf-8')

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def test_investigation(app, test_user):
    """Créer une investigation de test"""
    investigation = Investigation(
        name='Test Investigation',
        target_url='https://example.com',
        description='Test description',
        owner_id=test_user.id,
        is_public=False,
        is_collaborative=False
    )

    db.session.add(investigation)
    db.session.commit()

    return investigation


@pytest.fixture
def authenticated_client(client, test_user):
    """Client authentifié"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
    return client

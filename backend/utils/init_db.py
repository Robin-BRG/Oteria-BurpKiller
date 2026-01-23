# -*- coding: utf-8 -*-
"""
Script d'initialisation de la base de donnees
Equivalent a 'rails db:migrate' en Rails
"""
from app import app
from models import db

def init_database():
    """Cree toutes les tables dans la base de donnees"""
    with app.app_context():
        print("[--] Creation des tables...")
        db.create_all()
        print("[OK] Base de donnees initialisee avec succes!")
        print("[--] Tables creees: users")

if __name__ == '__main__':
    init_database()

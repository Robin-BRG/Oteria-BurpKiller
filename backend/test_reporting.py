# -*- coding: utf-8 -*-
"""
Script de test pour le systeme de reporting
"""
from app import app, db
from models import Investigation, User
from report_generator import generate_html_report, generate_pdf_report
import os

def test_reporting():
    """Tester la generation de rapports"""
    with app.app_context():
        # Recuperer une investigation existante
        investigation = Investigation.query.first()

        if not investigation:
            print("[ERREUR] Aucune investigation trouvee dans la base de donnees")
            print("         Creez d'abord une investigation via l'interface web")
            return False

        print(f"[OK] Investigation trouvee: {investigation.name}")
        print(f"     ID: {investigation.id}")
        print(f"     Cible: {investigation.target_url}")

        # Recuperer l'utilisateur
        user = investigation.owner
        print(f"[OK] Proprietaire: {user.username}")

        # Statistiques
        print(f"\n[STATS] Statistiques:")
        print(f"  - Scans web: {investigation.scans.count()}")
        print(f"  - Scans reseau: {investigation.network_scans.count()}")
        print(f"  - Scans AD: {investigation.ad_scans.count()}")
        print(f"  - Scans vulnerabilites: {investigation.vuln_scans.count()}")

        # Tester la generation HTML
        print(f"\n[TEST] Generation du rapport HTML...")
        try:
            html = generate_html_report(investigation, user)
            html_size = len(html)
            print(f"[OK] HTML genere: {html_size} octets")

            # Sauvegarder pour inspection
            html_path = f"rapport_test_{investigation.id}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[OK] Rapport sauvegarde: {html_path}")

        except Exception as e:
            print(f"[ERREUR] Erreur HTML: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Tester la generation PDF
        print(f"\n[TEST] Generation du rapport PDF...")
        try:
            pdf = generate_pdf_report(investigation, user)
            pdf_size = len(pdf)
            print(f"[OK] PDF genere: {pdf_size} octets")

            # Sauvegarder pour inspection
            pdf_path = f"rapport_test_{investigation.id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(pdf)
            print(f"[OK] Rapport sauvegarde: {pdf_path}")

        except Exception as e:
            print(f"[ERREUR] Erreur PDF: {e}")
            print("         Note: WeasyPrint peut necessiter GTK+ sur Windows")
            import traceback
            traceback.print_exc()
            return False

        print(f"\n[SUCCESS] Tests reussis!")
        print(f"          HTML: {html_path}")
        print(f"          PDF: {pdf_path}")
        return True

if __name__ == '__main__':
    test_reporting()

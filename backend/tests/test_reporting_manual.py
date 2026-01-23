# -*- coding: utf-8 -*-
"""
Tests pour le systeme de reporting
"""
import pytest
from models import Investigation, User
from blueprints.report_generator import generate_html_report, generate_pdf_report


class TestReporting:
    """Tests pour la generation de rapports"""

    def test_reporting(self, app, test_investigation, test_user):
        """Tester la generation de rapports"""
        # Recuperer l'investigation de test
        investigation = test_investigation
        user = test_user

        assert investigation is not None
        assert user is not None

        # Tester la generation HTML
        html = generate_html_report(investigation, user)
        assert html is not None
        assert len(html) > 0
        assert investigation.name in html
        assert user.username in html

    def test_html_report_structure(self, app, test_investigation, test_user):
        """Test de la structure du rapport HTML"""
        html = generate_html_report(test_investigation, test_user)

        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html

    def test_pdf_generation_or_fallback(self, app, test_investigation, test_user):
        """Test de generation PDF (peut echouer sur Windows sans GTK)"""
        try:
            pdf = generate_pdf_report(test_investigation, test_user)
            assert pdf is not None
            assert len(pdf) > 0
        except Exception as e:
            # WeasyPrint peut necessiter GTK+ sur Windows
            error_msg = str(e).lower()
            # C'est acceptable si l'erreur est liee a GTK/WeasyPrint
            assert 'gtk' in error_msg or 'gobject' in error_msg or 'weasyprint' in error_msg or 'cairo' in error_msg, f"Unexpected error: {e}"

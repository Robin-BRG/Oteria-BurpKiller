# -*- coding: utf-8 -*-
"""
Tests pour le module de génération de rapports
"""
import pytest
from blueprints.report_generator import generate_html_report


class TestReportGeneration:
    """Tests pour la génération de rapports"""

    def test_generate_html_report_basic(self, app, test_investigation, test_user):
        """Test de génération basique de rapport HTML"""
        html = generate_html_report(test_investigation, test_user)

        assert html is not None
        assert len(html) > 0
        assert isinstance(html, str)

    def test_html_report_contains_investigation_name(self, app, test_investigation, test_user):
        """Test que le rapport contient le nom de l'investigation"""
        html = generate_html_report(test_investigation, test_user)

        assert test_investigation.name in html

    def test_html_report_contains_target_url(self, app, test_investigation, test_user):
        """Test que le rapport contient l'URL cible"""
        html = generate_html_report(test_investigation, test_user)

        assert test_investigation.target_url in html

    def test_html_report_contains_owner(self, app, test_investigation, test_user):
        """Test que le rapport contient le propriétaire"""
        html = generate_html_report(test_investigation, test_user)

        assert test_user.username in html

    def test_html_report_structure(self, app, test_investigation, test_user):
        """Test de la structure HTML du rapport"""
        html = generate_html_report(test_investigation, test_user)

        # Vérifier les sections principales
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html
        assert 'Rapport de Pentest' in html
        assert 'Informations générales' in html or 'Informations generales' in html
        assert 'Résumé exécutif' in html or 'Resume executif' in html

    def test_html_report_has_css(self, app, test_investigation, test_user):
        """Test que le rapport a du CSS"""
        html = generate_html_report(test_investigation, test_user)

        assert '<style>' in html
        assert '</style>' in html

    def test_html_report_with_empty_investigation(self, app, test_user):
        """Test de génération de rapport pour investigation vide"""
        from models import db, Investigation

        empty_inv = Investigation(
            name='Empty Investigation',
            target_url='https://empty.com',
            owner_id=test_user.id
        )
        db.session.add(empty_inv)
        db.session.commit()

        html = generate_html_report(empty_inv, test_user)

        assert html is not None
        assert len(html) > 0
        assert empty_inv.name in html


class TestReportAPI:
    """Tests pour les routes API de reporting"""

    def test_get_html_report_authenticated(self, authenticated_client, test_investigation):
        """Test de récupération du rapport HTML authentifié"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/report/html'
        )

        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data

    def test_get_html_report_unauthenticated(self, client, test_investigation):
        """Test de récupération du rapport HTML non authentifié"""
        response = client.get(
            f'/api/investigations/{test_investigation.id}/report/html'
        )

        assert response.status_code == 401

    def test_get_report_preview(self, authenticated_client, test_investigation):
        """Test de l'aperçu du rapport"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/report/preview'
        )

        assert response.status_code == 200
        data = response.get_json()

        assert 'investigation' in data
        assert 'stats' in data
        assert data['investigation']['id'] == test_investigation.id

    def test_get_report_nonexistent_investigation(self, authenticated_client):
        """Test de rapport pour investigation inexistante"""
        response = authenticated_client.get('/api/investigations/99999/report/html')

        assert response.status_code == 404

    def test_report_preview_stats(self, authenticated_client, test_investigation):
        """Test des statistiques dans l'aperçu"""
        response = authenticated_client.get(
            f'/api/investigations/{test_investigation.id}/report/preview'
        )

        data = response.get_json()
        stats = data['stats']

        assert 'recon_scans' in stats
        assert 'network_scans' in stats
        assert 'ad_scans' in stats
        assert 'vuln_scans' in stats
        assert isinstance(stats['recon_scans'], int)

import { useState } from 'react';
import './ReportGenerator.css';

interface ReportGeneratorProps {
  investigationId: number;
  investigationName: string;
}

export default function ReportGenerator({ investigationId, investigationName }: ReportGeneratorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<any>(null);

  const fetchPreview = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:5000/api/investigations/${investigationId}/report/preview`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la récupération de l\'aperçu');
      }

      const data = await response.json();
      setPreview(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateHTML = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:5000/api/investigations/${investigationId}/report/html`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la génération du HTML');
      }

      // Créer un blob et télécharger le fichier
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_${investigationName.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.html`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generatePDF = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:5000/api/investigations/${investigationId}/report/pdf`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la génération du PDF');
      }

      // Créer un blob et télécharger le fichier
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rapport_${investigationName.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="report-generator">
      <div className="report-header">
        <h2>Génération de rapports</h2>
        <p className="report-description">
          Générez un rapport complet de cette investigation au format HTML ou PDF
        </p>
      </div>

      {error && (
        <div className="error-message">
          <strong>Erreur:</strong> {error}
        </div>
      )}

      <div className="report-actions">
        <button
          onClick={fetchPreview}
          disabled={loading}
          className="btn btn-secondary"
        >
          {loading ? 'Chargement...' : 'Aperçu des données'}
        </button>

        <button
          onClick={generateHTML}
          disabled={loading}
          className="btn btn-primary"
        >
          {loading ? 'Génération...' : 'Télécharger HTML'}
        </button>

        <button
          onClick={generatePDF}
          disabled={loading}
          className="btn btn-success"
        >
          {loading ? 'Génération...' : 'Télécharger PDF'}
        </button>
      </div>

      {preview && (
        <div className="report-preview">
          <h3>Aperçu du rapport</h3>

          <div className="preview-section">
            <h4>Investigation</h4>
            <div className="preview-grid">
              <div className="preview-item">
                <span className="preview-label">Nom:</span>
                <span className="preview-value">{preview.investigation.name}</span>
              </div>
              <div className="preview-item">
                <span className="preview-label">Cible:</span>
                <span className="preview-value">{preview.investigation.target_url}</span>
              </div>
              <div className="preview-item">
                <span className="preview-label">Créée le:</span>
                <span className="preview-value">{preview.investigation.created_at}</span>
              </div>
            </div>
          </div>

          <div className="preview-section">
            <h4>Statistiques</h4>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">{preview.stats.recon_scans}</div>
                <div className="stat-label">Scans Web</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{preview.stats.network_scans}</div>
                <div className="stat-label">Scans Réseau</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{preview.stats.ad_scans}</div>
                <div className="stat-label">Scans AD</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{preview.stats.total_vulnerabilities}</div>
                <div className="stat-label">Vulnérabilités</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{preview.stats.js_secrets}</div>
                <div className="stat-label">Secrets JS</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{preview.stats.http_requests}</div>
                <div className="stat-label">Requêtes HTTP</div>
              </div>
            </div>
          </div>

          <div className="preview-info">
            Le rapport inclura tous les résultats de scans, vulnérabilités détectées,
            secrets JavaScript, et informations collectées lors de cette investigation.
          </div>
        </div>
      )}
    </div>
  );
}

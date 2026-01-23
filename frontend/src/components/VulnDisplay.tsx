import { useState, useEffect } from 'react'
import './VulnDisplay.css'

interface VulnScan {
  id: number
  scan_type: string
  status: string
  progress_current: number
  progress_total: number
  vulnerabilities_count: number
  created_at: string
  completed_at: string | null
  error_message: string | null
}

interface Vulnerability {
  id: number
  vuln_type: string
  severity: string
  url: string
  parameter: string | null
  method: string
  payload: string | null
  evidence: string | null
  description: string | null
  recommendation: string | null
}

interface JsSecret {
  id: number
  secret_type: string
  severity: string
  source_url: string
  secret_preview: string | null
  context: string | null
  description: string | null
}

interface VulnDisplayProps {
  investigationId: number
}

function VulnDisplay({ investigationId }: VulnDisplayProps) {
  const [scans, setScans] = useState<VulnScan[]>([])
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([])
  const [jsSecrets, setJsSecrets] = useState<JsSecret[]>([])
  const [loading, setLoading] = useState(false)
  const [scanLoading, setScanLoading] = useState(false)
  const [activeScanId, setActiveScanId] = useState<number | null>(null)
  const [customUrl, setCustomUrl] = useState('')
  const [cookiesList, setCookiesList] = useState<{key: string, value: string}[]>([
    { key: '', value: '' }
  ])

  useEffect(() => {
    loadScans()
    loadJsSecrets()
  }, [investigationId])

  // Polling pour le scan actif
  useEffect(() => {
    if (activeScanId) {
      const interval = setInterval(() => {
        checkScanStatus(activeScanId)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeScanId])

  const loadScans = async () => {
    try {
      const res = await fetch(`http://localhost:5000/api/investigations/${investigationId}/vuln-scans`, {
        credentials: 'include'
      })
      if (res.ok) {
        const data = await res.json()
        setScans(data)

        // Charger les résultats du dernier scan complété
        const lastCompleted = data.find((s: VulnScan) => s.status === 'completed')
        if (lastCompleted) {
          loadVulnerabilities(lastCompleted.id)
        }
      }
    } catch (error) {
      console.error('Erreur chargement scans:', error)
    }
  }

  const loadVulnerabilities = async (scanId: number) => {
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:5000/api/vuln-scans/${scanId}/results`, {
        credentials: 'include'
      })
      if (res.ok) {
        const data = await res.json()
        setVulnerabilities(data.vulnerabilities || [])
      }
    } catch (error) {
      console.error('Erreur chargement vulns:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadJsSecrets = async () => {
    try {
      const res = await fetch(`http://localhost:5000/api/investigations/${investigationId}/js-secrets`, {
        credentials: 'include'
      })
      if (res.ok) {
        const data = await res.json()
        setJsSecrets(data)
      }
    } catch (error) {
      console.error('Erreur chargement secrets:', error)
    }
  }

  const checkScanStatus = async (scanId: number) => {
    try {
      const res = await fetch(`http://localhost:5000/api/vuln-scans/${scanId}`, {
        credentials: 'include'
      })
      if (res.ok) {
        const scan = await res.json()
        setScans(prev => prev.map(s => s.id === scanId ? scan : s))

        if (scan.status === 'completed' || scan.status === 'failed') {
          setActiveScanId(null)
          setScanLoading(false)
          if (scan.status === 'completed') {
            loadVulnerabilities(scanId)
          }
        }
      }
    } catch (error) {
      console.error('Erreur check status:', error)
    }
  }

  const addCookie = () => {
    setCookiesList([...cookiesList, { key: '', value: '' }])
  }

  const removeCookie = (index: number) => {
    if (cookiesList.length > 1) {
      setCookiesList(cookiesList.filter((_, i) => i !== index))
    }
  }

  const updateCookie = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...cookiesList]
    updated[index][field] = value
    setCookiesList(updated)
  }

  const buildCookiesString = (): string => {
    return cookiesList
      .filter(c => c.key.trim() && c.value.trim())
      .map(c => `${c.key.trim()}=${c.value.trim()}`)
      .join('; ')
  }

  const startScan = async (scanType: string) => {
    setScanLoading(true)
    const cookiesStr = buildCookiesString()
    try {
      const res = await fetch(`http://localhost:5000/api/investigations/${investigationId}/vuln-scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          scan_type: scanType,
          custom_url: customUrl || undefined,
          cookies: cookiesStr || undefined
        })
      })

      if (res.ok) {
        const scan = await res.json()
        setScans(prev => [scan, ...prev])
        setActiveScanId(scan.id)
      }
    } catch (error) {
      console.error('Erreur démarrage scan:', error)
      setScanLoading(false)
    }
  }

  const startJsScan = async () => {
    try {
      await fetch(`http://localhost:5000/api/investigations/${investigationId}/js-scan`, {
        method: 'POST',
        credentials: 'include'
      })
      setTimeout(loadJsSecrets, 3000) // Recharger après 3 secondes
    } catch (error) {
      console.error('Erreur scan JS:', error)
    }
  }

  const getSeverityClass = (severity: string): string => {
    switch (severity) {
      case 'critical': return 'severity-critical'
      case 'high': return 'severity-high'
      case 'medium': return 'severity-medium'
      case 'low': return 'severity-low'
      default: return 'severity-info'
    }
  }

  const groupedVulns = vulnerabilities.reduce((acc, vuln) => {
    if (!acc[vuln.vuln_type]) {
      acc[vuln.vuln_type] = []
    }
    acc[vuln.vuln_type].push(vuln)
    return acc
  }, {} as Record<string, Vulnerability[]>)

  const activeScan = scans.find(s => s.id === activeScanId)

  return (
    <div className="vuln-display">
      {/* Boutons de scan */}
      <div className="scan-controls">
        <h3 className="section-title">Scanners de Vulnerabilites</h3>

        {/* Options avancees */}
        <div className="scan-options">
          <div className="option-group">
            <label htmlFor="custom-url">URL personnalisee (avec parametres)</label>
            <input
              id="custom-url"
              type="text"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="http://localhost:8080/vulnerabilities/sqli/?id=1&Submit=Submit"
              className="scan-input"
            />
          </div>
          <div className="option-group">
            <label>Cookies (pour authentification)</label>
            <div className="cookies-list">
              {cookiesList.map((cookie, index) => (
                <div key={index} className="cookie-row">
                  <input
                    type="text"
                    value={cookie.key}
                    onChange={(e) => updateCookie(index, 'key', e.target.value)}
                    placeholder="PHPSESSID"
                    className="scan-input cookie-key"
                  />
                  <span className="cookie-separator">=</span>
                  <input
                    type="text"
                    value={cookie.value}
                    onChange={(e) => updateCookie(index, 'value', e.target.value)}
                    placeholder="abc123..."
                    className="scan-input cookie-value"
                  />
                  <button
                    type="button"
                    className="cookie-remove"
                    onClick={() => removeCookie(index)}
                    disabled={cookiesList.length === 1}
                  >
                    x
                  </button>
                </div>
              ))}
              <button type="button" className="cookie-add" onClick={addCookie}>
                + Ajouter un cookie
              </button>
            </div>
          </div>
        </div>

        <div className="scan-buttons">
          <button
            className="scan-button sqli"
            onClick={() => startScan('sqli')}
            disabled={scanLoading}
          >
            Scanner SQLi
          </button>
          <button
            className="scan-button xss"
            onClick={() => startScan('xss')}
            disabled={scanLoading}
          >
            Scanner XSS
          </button>
          <button
            className="scan-button all"
            onClick={() => startScan('all')}
            disabled={scanLoading}
          >
            Scanner Complet
          </button>
          <button
            className="scan-button js"
            onClick={startJsScan}
          >
            Scanner JavaScript
          </button>
        </div>

        {activeScan && activeScan.status === 'running' && (
          <div className="scan-progress">
            <div className="progress-info">
              Scan en cours: {activeScan.scan_type.toUpperCase()}
              {activeScan.progress_total > 0 && (
                <span> - {activeScan.progress_current}/{activeScan.progress_total}</span>
              )}
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: activeScan.progress_total > 0
                    ? `${(activeScan.progress_current / activeScan.progress_total) * 100}%`
                    : '0%'
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Vulnerabilites trouvees */}
      {vulnerabilities.length > 0 && (
        <div className="vulns-section">
          <h3 className="section-title">
            Vulnerabilites Detectees ({vulnerabilities.length})
          </h3>

          {Object.entries(groupedVulns).map(([vulnType, vulns]) => (
            <div key={vulnType} className="vuln-type-group">
              <h4 className="vuln-type-title">
                {vulnType.toUpperCase()} ({vulns.length})
              </h4>

              {vulns.map(vuln => (
                <div key={vuln.id} className="vuln-card">
                  <div className="vuln-header">
                    <span className={`severity-badge ${getSeverityClass(vuln.severity)}`}>
                      {vuln.severity.toUpperCase()}
                    </span>
                    <span className="vuln-url">{vuln.url}</span>
                  </div>

                  {vuln.parameter && (
                    <div className="vuln-detail">
                      <strong>Parametre vulnerable:</strong> {vuln.parameter} ({vuln.method})
                    </div>
                  )}

                  {vuln.description && (
                    <div className="vuln-detail">
                      <strong>Description:</strong> {vuln.description}
                    </div>
                  )}

                  {vuln.payload && (
                    <div className="vuln-detail">
                      <strong>Payload:</strong>
                      <pre className="payload-code">{vuln.payload}</pre>
                    </div>
                  )}

                  {vuln.evidence && (
                    <div className="vuln-detail">
                      <strong>Preuve:</strong>
                      <pre className="evidence-code">{vuln.evidence}</pre>
                    </div>
                  )}

                  {vuln.recommendation && (
                    <div className="vuln-recommendation">
                      <strong>Recommendation:</strong> {vuln.recommendation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Secrets JavaScript */}
      {jsSecrets.length > 0 && (
        <div className="secrets-section">
          <h3 className="section-title">
            Secrets Trouves dans JavaScript ({jsSecrets.length})
          </h3>

          {jsSecrets.map(secret => (
            <div key={secret.id} className="secret-card">
              <div className="secret-header">
                <span className={`severity-badge ${getSeverityClass(secret.severity)}`}>
                  {secret.severity.toUpperCase()}
                </span>
                <span className="secret-type">{secret.secret_type.replace(/_/g, ' ').toUpperCase()}</span>
              </div>

              {secret.description && (
                <div className="secret-detail">
                  <strong>Description:</strong> {secret.description}
                </div>
              )}

              <div className="secret-detail">
                <strong>Source:</strong>
                <code className="source-url">{secret.source_url}</code>
              </div>

              {secret.secret_preview && (
                <div className="secret-detail">
                  <strong>Valeur:</strong>
                  <code className="secret-value">{secret.secret_preview}</code>
                </div>
              )}

              {secret.context && (
                <div className="secret-detail">
                  <strong>Contexte:</strong>
                  <pre className="context-code">{secret.context}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {vulnerabilities.length === 0 && jsSecrets.length === 0 && !loading && (
        <div className="empty-state">
          <p>Aucune vulnerabilite detectee</p>
          <p className="hint">Lancez un scan pour detecter des vulnerabilites SQLi, XSS ou des secrets JavaScript</p>
        </div>
      )}
    </div>
  )
}

export default VulnDisplay

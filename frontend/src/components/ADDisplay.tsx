import { useState, useEffect } from 'react'
import './ADDisplay.css'

interface ADScan {
  id: number
  target: string
  domain: string | null
  scan_type: string
  status: string
  progress_current: number
  progress_total: number
  results_count: number
  created_at: string
  completed_at: string | null
  error_message: string | null
}

interface ADResult {
  id: number
  result_type: string
  name: string
  value: string | null
  severity: string
  port: number | null
  service: string | null
  description: string | null
}

interface DCDetection {
  is_dc: boolean
  confidence: number
  indicators: string[]
  open_ports: { port: number; service: string; state: string }[]
}

interface ADDisplayProps {
  investigationId: number
  targetHost?: string
}

function ADDisplay({ investigationId, targetHost }: ADDisplayProps) {
  const [scans, setScans] = useState<ADScan[]>([])
  const [results, setResults] = useState<ADResult[]>([])
  const [activeScan, setActiveScan] = useState<ADScan | null>(null)
  const [loading, setLoading] = useState(false)
  const [showScanModal, setShowScanModal] = useState(false)
  const [dcDetection, setDcDetection] = useState<DCDetection | null>(null)
  const [detecting, setDetecting] = useState(false)

  // Config du scan
  const [scanTarget, setScanTarget] = useState(targetHost || '')
  const [scanType, setScanType] = useState<'basic' | 'full'>('basic')
  const [domain, setDomain] = useState('')

  const API_URL = ''

  useEffect(() => {
    loadScans()
  }, [investigationId])

  useEffect(() => {
    if (activeScan && activeScan.status === 'running') {
      const interval = setInterval(() => {
        checkScanStatus(activeScan.id)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeScan])

  const loadScans = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/ad-scans`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setScans(data)

        const lastCompleted = data.find((s: ADScan) => s.status === 'completed')
        if (lastCompleted) {
          loadResults(lastCompleted.id)
        }

        const running = data.find((s: ADScan) => s.status === 'running')
        if (running) {
          setActiveScan(running)
        }
      }
    } catch (error) {
      console.error('Erreur chargement scans:', error)
    }
  }

  const loadResults = async (scanId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/ad-scans/${scanId}/results`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setResults(data.results)
      }
    } catch (error) {
      console.error('Erreur chargement resultats:', error)
    }
  }

  const checkScanStatus = async (scanId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/ad-scans/${scanId}`, {
        credentials: 'include'
      })
      if (response.ok) {
        const scan = await response.json()
        if (scan.status === 'completed') {
          setActiveScan(null)
          loadScans()
          loadResults(scanId)
        } else if (scan.status === 'failed') {
          setActiveScan(null)
          loadScans()
        } else {
          setActiveScan(scan)
        }
      }
    } catch (error) {
      console.error('Erreur verification scan:', error)
    }
  }

  const detectDC = async () => {
    if (!scanTarget) return

    setDetecting(true)
    try {
      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/detect-dc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ target: scanTarget })
      })

      if (response.ok) {
        const data = await response.json()
        setDcDetection(data)
      }
    } catch (error) {
      console.error('Erreur detection DC:', error)
    } finally {
      setDetecting(false)
    }
  }

  const startScan = async () => {
    if (!scanTarget) return

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/ad-scans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          target: scanTarget,
          scan_type: scanType,
          domain: domain
        })
      })

      if (response.ok) {
        const scan = await response.json()
        setActiveScan(scan)
        setShowScanModal(false)
        loadScans()
      }
    } catch (error) {
      console.error('Erreur lancement scan:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityClass = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'severity-critical'
      case 'high': return 'severity-high'
      case 'medium': return 'severity-medium'
      case 'low': return 'severity-low'
      default: return 'severity-info'
    }
  }

  const getResultTypeIcon = (type: string): string => {
    switch (type) {
      case 'port': return '🔌'
      case 'ldap_info': return '📂'
      case 'vulnerability': return '⚠️'
      case 'detection': return '🎯'
      case 'kerberos_info': return '🔐'
      case 'smb_info': return '📁'
      default: return 'ℹ️'
    }
  }

  // Grouper les resultats par type
  const groupedResults = results.reduce((acc, r) => {
    const key = r.result_type
    if (!acc[key]) {
      acc[key] = []
    }
    acc[key].push(r)
    return acc
  }, {} as Record<string, ADResult[]>)

  const vulnerabilities = results.filter(r => r.result_type === 'vulnerability')
  const ports = results.filter(r => r.result_type === 'port')
  const info = results.filter(r => !['vulnerability', 'port'].includes(r.result_type))

  return (
    <div className="ad-display">
      <div className="ad-header">
        <h3>Active Directory</h3>
        <div className="ad-actions">
          <button
            className="btn btn-secondary"
            onClick={() => setShowScanModal(true)}
          >
            Detection DC
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setShowScanModal(true)}
            disabled={activeScan !== null}
          >
            {activeScan ? 'Scan en cours...' : 'Nouveau scan AD'}
          </button>
        </div>
      </div>

      {activeScan && (
        <div className="scan-progress">
          <span className="progress-spinner"></span>
          <span>Scan AD en cours sur {activeScan.target}</span>
          {activeScan.progress_total > 0 && (
            <div className="progress-bar">
              <div
                className="progress-bar-fill"
                style={{ width: `${(activeScan.progress_current / activeScan.progress_total) * 100}%` }}
              />
            </div>
          )}
        </div>
      )}

      {dcDetection && (
        <div className={`dc-detection ${dcDetection.is_dc ? 'is-dc' : 'not-dc'}`}>
          <div className="dc-detection-header">
            <span className="dc-icon">{dcDetection.is_dc ? '✅' : '❌'}</span>
            <span className="dc-status">
              {dcDetection.is_dc ? 'Domain Controller detecte' : 'Probablement pas un DC'}
            </span>
            <span className="dc-confidence">Confiance: {dcDetection.confidence}%</span>
          </div>
          {dcDetection.indicators.length > 0 && (
            <div className="dc-indicators">
              {dcDetection.indicators.map((ind, i) => (
                <span key={i} className="indicator-badge">{ind}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {results.length > 0 ? (
        <div className="ad-results">
          {vulnerabilities.length > 0 && (
            <div className="results-section vulnerabilities">
              <h4>Vulnerabilites detectees ({vulnerabilities.length})</h4>
              <div className="results-list">
                {vulnerabilities.map(vuln => (
                  <div key={vuln.id} className={`result-card ${getSeverityClass(vuln.severity)}`}>
                    <div className="result-header">
                      <span className="result-icon">{getResultTypeIcon(vuln.result_type)}</span>
                      <span className="result-name">{vuln.name}</span>
                      <span className={`severity-badge ${getSeverityClass(vuln.severity)}`}>
                        {vuln.severity}
                      </span>
                    </div>
                    {vuln.value && <p className="result-value">{vuln.value}</p>}
                    {vuln.description && <p className="result-description">{vuln.description}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {ports.length > 0 && (
            <div className="results-section ports">
              <h4>Ports AD ouverts ({ports.length})</h4>
              <div className="ports-grid">
                {ports.map(port => (
                  <div key={port.id} className="port-card">
                    <span className="port-number">{port.port}</span>
                    <span className="port-service">{port.service}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {info.length > 0 && (
            <div className="results-section info">
              <h4>Informations collectees ({info.length})</h4>
              <div className="results-list">
                {info.map(item => (
                  <div key={item.id} className="result-card info">
                    <div className="result-header">
                      <span className="result-icon">{getResultTypeIcon(item.result_type)}</span>
                      <span className="result-name">{item.name}</span>
                      <span className="result-type-badge">{item.result_type}</span>
                    </div>
                    {item.value && <p className="result-value mono">{item.value}</p>}
                    {item.description && <p className="result-description">{item.description}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="no-results">
          <p>Aucun resultat de scan Active Directory</p>
          <p className="hint">Lancez un scan pour enumerer le domaine AD</p>
        </div>
      )}

      {scans.length > 0 && (
        <div className="scans-history">
          <h4>Historique des scans AD</h4>
          <ul className="scans-list">
            {scans.slice(0, 5).map(scan => (
              <li
                key={scan.id}
                className={`scan-item ${scan.status}`}
                onClick={() => scan.status === 'completed' && loadResults(scan.id)}
              >
                <span className="scan-target">{scan.target}</span>
                {scan.domain && <span className="scan-domain">{scan.domain}</span>}
                <span className="scan-type">{scan.scan_type}</span>
                <span className="scan-status">{scan.status}</span>
                <span className="scan-count">{scan.results_count} resultats</span>
                <span className="scan-date">{new Date(scan.created_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {showScanModal && (
        <div className="modal-overlay" onClick={() => setShowScanModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Scan Active Directory</h2>

            <div className="form-group">
              <label>Cible (IP ou hostname du DC)</label>
              <input
                type="text"
                value={scanTarget}
                onChange={e => setScanTarget(e.target.value)}
                placeholder="dc01.domain.local ou 192.168.1.10"
              />
            </div>

            <div className="form-group">
              <label>Domaine (optionnel)</label>
              <input
                type="text"
                value={domain}
                onChange={e => setDomain(e.target.value)}
                placeholder="domain.local"
              />
            </div>

            <div className="form-group">
              <button
                className="btn btn-secondary btn-block"
                onClick={detectDC}
                disabled={detecting || !scanTarget}
              >
                {detecting ? 'Detection...' : 'Detecter si c\'est un DC'}
              </button>
            </div>

            <div className="form-group">
              <label>Type de scan</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="scanType"
                    value="basic"
                    checked={scanType === 'basic'}
                    onChange={() => setScanType('basic')}
                  />
                  <span>Basic (ports AD + LDAP anonyme)</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="scanType"
                    value="full"
                    checked={scanType === 'full'}
                    onChange={() => setScanType('full')}
                  />
                  <span>Full (+ SMB + Kerberos checks)</span>
                </label>
              </div>
            </div>

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowScanModal(false)}>
                Annuler
              </button>
              <button
                className="btn btn-primary"
                onClick={startScan}
                disabled={loading || !scanTarget}
              >
                {loading ? 'Lancement...' : 'Lancer le scan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ADDisplay

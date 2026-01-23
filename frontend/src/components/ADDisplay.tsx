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

interface BloodHoundAnalysis {
  id: number
  investigation_id: number
  name: string
  domain: string | null
  users_count: number
  computers_count: number
  groups_count: number
  domains_count: number
  status: string
  error_message: string | null
  started_by: any
  created_at: string
  completed_at: string | null
  findings_count: number
  files_count: number
}

interface BloodHoundFinding {
  id: number
  analysis_id: number
  category: string
  severity: string
  title: string
  description: string | null
  affected_objects: any
  attack_path: any
  recommendation: string | null
  references: any
  created_at: string
}

interface ADDisplayProps {
  investigationId: number
  targetHost?: string
}

function ADDisplay({ investigationId, targetHost }: ADDisplayProps) {
  // Tab actif: 'scans' ou 'bloodhound'
  const [activeTab, setActiveTab] = useState<'scans' | 'bloodhound'>('bloodhound')

  // AD Scans
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

  // BloodHound
  const [bhAnalyses, setBhAnalyses] = useState<BloodHoundAnalysis[]>([])
  const [activeAnalysis, setActiveAnalysis] = useState<BloodHoundAnalysis | null>(null)
  const [bhFindings, setBhFindings] = useState<BloodHoundFinding[]>([])
  const [bhSummary, setBhSummary] = useState<any>(null)
  const [bhLoading, setBhLoading] = useState(false)
  const [showBhUpload, setShowBhUpload] = useState(false)
  const [bhFiles, setBhFiles] = useState<FileList | null>(null)
  const [bhAnalysisName, setBhAnalysisName] = useState('')
  const [bhFilterCategory, setBhFilterCategory] = useState<string>('all')
  const [bhFilterSeverity, setBhFilterSeverity] = useState<string>('all')

  const API_URL = ''

  useEffect(() => {
    loadScans()
    loadBloodHoundAnalyses()
  }, [investigationId])

  useEffect(() => {
    if (activeScan && activeScan.status === 'running') {
      const interval = setInterval(() => {
        checkScanStatus(activeScan.id)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeScan])

  useEffect(() => {
    if (activeAnalysis && activeAnalysis.status === 'running') {
      const interval = setInterval(() => {
        checkBloodHoundStatus(activeAnalysis.id)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeAnalysis])

  useEffect(() => {
    if (activeAnalysis && activeAnalysis.status === 'completed') {
      loadBloodHoundFindings(activeAnalysis.id)
    }
  }, [activeAnalysis])

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

  // ============================================================================
  // BLOODHOUND FUNCTIONS
  // ============================================================================

  const loadBloodHoundAnalyses = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/bloodhound`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setBhAnalyses(data)

        // Selectionner la derniere analyse completee
        const lastCompleted = data.find((a: BloodHoundAnalysis) => a.status === 'completed')
        if (lastCompleted) {
          setActiveAnalysis(lastCompleted)
        }

        // Verifier si une analyse est en cours
        const running = data.find((a: BloodHoundAnalysis) => a.status === 'running')
        if (running) {
          setActiveAnalysis(running)
        }
      }
    } catch (error) {
      console.error('Erreur chargement analyses BloodHound:', error)
    }
  }

  const checkBloodHoundStatus = async (analysisId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/bloodhound/${analysisId}`, {
        credentials: 'include'
      })
      if (response.ok) {
        const analysis = await response.json()
        if (analysis.status === 'completed') {
          loadBloodHoundAnalyses()
          loadBloodHoundFindings(analysisId)
        } else if (analysis.status === 'failed') {
          setActiveAnalysis(null)
          loadBloodHoundAnalyses()
        } else {
          setActiveAnalysis(analysis)
        }
      }
    } catch (error) {
      console.error('Erreur verification analyse:', error)
    }
  }

  const loadBloodHoundFindings = async (analysisId: number) => {
    try {
      let url = `${API_URL}/api/bloodhound/${analysisId}/findings?`
      if (bhFilterCategory !== 'all') url += `category=${bhFilterCategory}&`
      if (bhFilterSeverity !== 'all') url += `severity=${bhFilterSeverity}&`

      const response = await fetch(url, { credentials: 'include' })
      if (response.ok) {
        const data = await response.json()
        setBhFindings(data.findings)
        setBhSummary(data.summary)
      }
    } catch (error) {
      console.error('Erreur chargement findings:', error)
    }
  }

  const uploadBloodHoundFiles = async () => {
    if (!bhFiles || bhFiles.length === 0) return

    setBhLoading(true)
    try {
      const formData = new FormData()
      Array.from(bhFiles).forEach(file => {
        formData.append('files', file)
      })
      if (bhAnalysisName) {
        formData.append('name', bhAnalysisName)
      }

      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/bloodhound`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setActiveAnalysis(data.analysis)
        setShowBhUpload(false)
        setBhFiles(null)
        setBhAnalysisName('')
        loadBloodHoundAnalyses()
      } else {
        const error = await response.json()
        alert(`Erreur: ${error.error}`)
      }
    } catch (error) {
      console.error('Erreur upload BloodHound:', error)
      alert('Erreur lors de l\'upload')
    } finally {
      setBhLoading(false)
    }
  }

  const deleteBloodHoundAnalysis = async (analysisId: number) => {
    if (!confirm('Supprimer cette analyse BloodHound?')) return

    try {
      const response = await fetch(`${API_URL}/api/bloodhound/${analysisId}`, {
        method: 'DELETE',
        credentials: 'include'
      })

      if (response.ok) {
        if (activeAnalysis?.id === analysisId) {
          setActiveAnalysis(null)
          setBhFindings([])
          setBhSummary(null)
        }
        loadBloodHoundAnalyses()
      }
    } catch (error) {
      console.error('Erreur suppression analyse:', error)
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

  // Categories BloodHound
  const bhCategories = Array.from(new Set(bhFindings.map(f => f.category)))

  return (
    <div className="ad-display">
      <div className="ad-header">
        <h3>Active Directory</h3>
        <div className="ad-tabs">
          <button
            className={`tab-btn ${activeTab === 'scans' ? 'active' : ''}`}
            onClick={() => setActiveTab('scans')}
          >
            Scans AD
          </button>
          <button
            className={`tab-btn ${activeTab === 'bloodhound' ? 'active' : ''}`}
            onClick={() => setActiveTab('bloodhound')}
          >
            BloodHound
            {bhAnalyses.length > 0 && <span className="tab-badge">{bhAnalyses.length}</span>}
          </button>
        </div>
        <div className="ad-actions">
          {activeTab === 'scans' ? (
            <>
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
            </>
          ) : (
            <button
              className="btn btn-primary"
              onClick={() => setShowBhUpload(true)}
              disabled={activeAnalysis?.status === 'running'}
            >
              Upload BloodHound
            </button>
          )}
        </div>
      </div>

      {activeTab === 'scans' && activeScan && (
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

      {activeTab === 'bloodhound' && activeAnalysis && activeAnalysis.status === 'running' && (
        <div className="scan-progress">
          <span className="progress-spinner"></span>
          <span>Analyse BloodHound en cours...</span>
        </div>
      )}

      {/* TAB: AD SCANS */}
      {activeTab === 'scans' && (
        <>
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
        </>
      )}

      {/* TAB: BLOODHOUND */}
      {activeTab === 'bloodhound' && (
        <>
          {bhAnalyses.length === 0 ? (
            <div className="no-results">
              <p>Aucune analyse BloodHound</p>
              <p className="hint">Uploadez des fichiers BloodHound (JSON ou ZIP) pour commencer l'analyse</p>
              <button className="btn btn-primary" onClick={() => setShowBhUpload(true)}>
                Upload BloodHound
              </button>
            </div>
          ) : (
            <>
              {/* Sélecteur d'analyse */}
              <div className="bh-analyses-selector">
                <label>Analyse:</label>
                <select
                  value={activeAnalysis?.id || ''}
                  onChange={e => {
                    const analysis = bhAnalyses.find(a => a.id === Number(e.target.value))
                    setActiveAnalysis(analysis || null)
                  }}
                  className="bh-select"
                >
                  {bhAnalyses.map(analysis => (
                    <option key={analysis.id} value={analysis.id}>
                      {analysis.name} - {analysis.domain || 'Unknown'} ({analysis.status})
                    </option>
                  ))}
                </select>
                {activeAnalysis && activeAnalysis.status === 'completed' && (
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => deleteBloodHoundAnalysis(activeAnalysis.id)}
                  >
                    Supprimer
                  </button>
                )}
              </div>

              {activeAnalysis && activeAnalysis.status === 'completed' && (
                <>
                  {/* Statistiques */}
                  <div className="bh-stats">
                    <div className="stat-card">
                      <span className="stat-value">{activeAnalysis.users_count}</span>
                      <span className="stat-label">Users</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{activeAnalysis.computers_count}</span>
                      <span className="stat-label">Computers</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{activeAnalysis.groups_count}</span>
                      <span className="stat-label">Groups</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{activeAnalysis.domains_count}</span>
                      <span className="stat-label">Domains</span>
                    </div>
                    <div className="stat-card">
                      <span className="stat-value">{activeAnalysis.findings_count}</span>
                      <span className="stat-label">Findings</span>
                    </div>
                  </div>

                  {/* Résumé par sévérité */}
                  {bhSummary && (
                    <div className="bh-summary">
                      {bhSummary.critical > 0 && (
                        <div className="summary-badge critical">
                          Critical: {bhSummary.critical}
                        </div>
                      )}
                      {bhSummary.high > 0 && (
                        <div className="summary-badge high">
                          High: {bhSummary.high}
                        </div>
                      )}
                      {bhSummary.medium > 0 && (
                        <div className="summary-badge medium">
                          Medium: {bhSummary.medium}
                        </div>
                      )}
                      {bhSummary.low > 0 && (
                        <div className="summary-badge low">
                          Low: {bhSummary.low}
                        </div>
                      )}
                      {bhSummary.info > 0 && (
                        <div className="summary-badge info">
                          Info: {bhSummary.info}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Filtres */}
                  <div className="bh-filters">
                    <div className="filter-group">
                      <label>Catégorie:</label>
                      <select
                        value={bhFilterCategory}
                        onChange={e => {
                          setBhFilterCategory(e.target.value)
                          if (activeAnalysis) loadBloodHoundFindings(activeAnalysis.id)
                        }}
                      >
                        <option value="all">Toutes</option>
                        {bhCategories.map(cat => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                    </div>
                    <div className="filter-group">
                      <label>Sévérité:</label>
                      <select
                        value={bhFilterSeverity}
                        onChange={e => {
                          setBhFilterSeverity(e.target.value)
                          if (activeAnalysis) loadBloodHoundFindings(activeAnalysis.id)
                        }}
                      >
                        <option value="all">Toutes</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                        <option value="info">Info</option>
                      </select>
                    </div>
                  </div>

                  {/* Findings */}
                  <div className="bh-findings">
                    {bhFindings.length > 0 ? (
                      bhFindings.map(finding => (
                        <div key={finding.id} className={`finding-card ${getSeverityClass(finding.severity)}`}>
                          <div className="finding-header">
                            <div className="finding-title-row">
                              <span className="finding-title">{finding.title}</span>
                              <span className={`severity-badge ${getSeverityClass(finding.severity)}`}>
                                {finding.severity}
                              </span>
                            </div>
                            <span className="finding-category">{finding.category}</span>
                          </div>
                          {finding.description && (
                            <p className="finding-description">{finding.description}</p>
                          )}
                          {finding.affected_objects && (
                            <div className="finding-objects">
                              <strong>Objets affectés:</strong>
                              <pre>{JSON.stringify(finding.affected_objects, null, 2)}</pre>
                            </div>
                          )}
                          {finding.attack_path && (
                            <div className="finding-path">
                              <strong>Chemin d'attaque:</strong>
                              <div className="attack-path">
                                {finding.attack_path.map((node: string, i: number) => (
                                  <span key={i}>
                                    {node}
                                    {i < finding.attack_path.length - 1 && ' → '}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {finding.recommendation && (
                            <div className="finding-recommendation">
                              <strong>Recommandation:</strong> {finding.recommendation}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="no-findings">
                        <p>Aucun finding trouvé avec ces filtres</p>
                      </div>
                    )}
                  </div>
                </>
              )}

              {activeAnalysis && activeAnalysis.status === 'failed' && (
                <div className="error-message">
                  <p>Erreur lors de l'analyse:</p>
                  <pre>{activeAnalysis.error_message}</pre>
                </div>
              )}
            </>
          )}
        </>
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

      {showBhUpload && (
        <div className="modal-overlay" onClick={() => setShowBhUpload(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Upload BloodHound</h2>

            <div className="form-group">
              <label>Nom de l'analyse (optionnel)</label>
              <input
                type="text"
                value={bhAnalysisName}
                onChange={e => setBhAnalysisName(e.target.value)}
                placeholder="Analyse du 23/01/2026"
              />
            </div>

            <div className="form-group">
              <label>Fichiers BloodHound (JSON ou ZIP)</label>
              <input
                type="file"
                multiple
                accept=".json,.zip"
                onChange={e => setBhFiles(e.target.files)}
              />
              {bhFiles && bhFiles.length > 0 && (
                <div className="files-list">
                  <p>{bhFiles.length} fichier(s) sélectionné(s):</p>
                  <ul>
                    {Array.from(bhFiles).map((file, i) => (
                      <li key={i}>{file.name} ({Math.round(file.size / 1024)} KB)</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="info-box">
              <p>Formats supportés:</p>
              <ul>
                <li>Fichiers JSON individuels (users, computers, groups, domains)</li>
                <li>Archives ZIP contenant plusieurs fichiers JSON</li>
                <li>Format BloodHound v4+ avec structure data/meta</li>
              </ul>
            </div>

            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowBhUpload(false)}>
                Annuler
              </button>
              <button
                className="btn btn-primary"
                onClick={uploadBloodHoundFiles}
                disabled={bhLoading || !bhFiles || bhFiles.length === 0}
              >
                {bhLoading ? 'Upload en cours...' : 'Upload et analyser'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ADDisplay

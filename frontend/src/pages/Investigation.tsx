import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ReconGraph from '../components/ReconGraph'
import ReconList from '../components/ReconList'
import EnumDisplay from '../components/EnumDisplay'
import RequestBuilder from '../components/RequestBuilder'
import HttpHistory from '../components/HttpHistory'
import VulnDisplay from '../components/VulnDisplay'
import type { ReconResult } from '../components/ReconGraph'
import type { EnumResult } from '../components/EnumDisplay'
import './Investigation.css'

interface InvestigationData {
  id: number
  name: string
  target_url: string
  description: string
  is_public: boolean
  is_collaborative: boolean
  owner: {
    id: number
    username: string
  }
  created_at: string
}

interface FileData {
  id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  uploaded_by: {
    username: string
  }
  created_at: string
}

interface ReconScan {
  id: number
  scan_mode: string
  status: string
  results_count: number
  progress_current: number
  progress_total: number
  created_at: string
}

interface EnumScan {
  id: number
  status: string
  results_count: number
  created_at: string
}

// Configuration de scan avancee
interface ScanConfig {
  tool: 'builtin' | 'gobuster' | 'feroxbuster' | 'custom'
  mode: 'stealth' | 'normal' | 'aggressive'
  wordlist: 'common' | 'medium' | 'large' | 'custom'
  customWordlist: string
  threads: number
  extensions: string
  userAgent: string
  cookies: string
  customHeaders: string
  timeout: number
  followRedirects: boolean
  customFlags: string
}

const DEFAULT_SCAN_CONFIG: ScanConfig = {
  tool: 'builtin',
  mode: 'normal',
  wordlist: 'common',
  customWordlist: '',
  threads: 10,
  extensions: '',
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  cookies: '',
  customHeaders: '',
  timeout: 10,
  followRedirects: false,
  customFlags: ''
}

// Onglets disponibles
const TABS = [
  { id: 'general', label: 'General' },
  { id: 'recon', label: 'Reconnaissance' },
  { id: 'enum', label: 'Enumeration' },
  { id: 'exploit', label: 'Exploitation' },
  { id: 'rapport', label: 'Rapport' }
]

// Helper pour obtenir la classe de status
function getStatusClass(status: number | null): string {
  if (!status) return ''
  if (status >= 200 && status < 300) return 'success'
  if (status >= 300 && status < 400) return 'redirect'
  if (status >= 400 && status < 500) return 'client-error'
  if (status >= 500) return 'server-error'
  return ''
}

// Helper pour obtenir le texte de status
function getStatusText(status: number | null): string {
  if (!status) return 'Inconnu'
  if (status >= 200 && status < 300) return 'Succes'
  if (status >= 300 && status < 400) return 'Redirection'
  if (status >= 400 && status < 500) return 'Erreur client'
  if (status >= 500) return 'Erreur serveur'
  return 'Inconnu'
}

// Helper pour formater la taille de fichier
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Helper pour verifier si un fichier est une image
function isImageFile(fileType: string): boolean {
  return ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(fileType.toLowerCase())
}

// Helper pour verifier si un fichier est du texte
function isTextFile(fileType: string): boolean {
  return ['txt', 'json', 'xml', 'csv', 'html', 'css', 'js', 'md', 'log'].includes(fileType.toLowerCase())
}

function Investigation() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const API_URL = ''

  const [investigation, setInvestigation] = useState<InvestigationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('general')

  // Fichiers partages
  const [files, setFiles] = useState<FileData[]>([])
  const [showFilesPanel, setShowFilesPanel] = useState(false)
  const [selectedFile, setSelectedFile] = useState<FileData | null>(null)
  const [fileContent, setFileContent] = useState<string | null>(null)
  const [showFileModal, setShowFileModal] = useState(false)
  const [renameValue, setRenameValue] = useState('')
  const [isRenaming, setIsRenaming] = useState(false)

  // Reconnaissance
  const [scans, setScans] = useState<ReconScan[]>([])
  const [reconResults, setReconResults] = useState<ReconResult[]>([])
  const [showScanModal, setShowScanModal] = useState(false)
  const [scanConfig, setScanConfig] = useState<ScanConfig>(DEFAULT_SCAN_CONFIG)
  const [showAdvancedScan, setShowAdvancedScan] = useState(false)
  const [scanLoading, setScanLoading] = useState(false)
  const [activeScan, setActiveScan] = useState<ReconScan | null>(null)
  const [reconView, setReconView] = useState<'graph' | 'list'>('graph')

  // Noeud selectionne pour le panel de details
  const [selectedNode, setSelectedNode] = useState<ReconResult | null>(null)

  // Enumeration
  const [enumScans, setEnumScans] = useState<EnumScan[]>([])
  const [enumResults, setEnumResults] = useState<EnumResult[]>([])
  const [enumLoading, setEnumLoading] = useState(false)
  const [activeEnumScan, setActiveEnumScan] = useState<EnumScan | null>(null)

  // HTTP Requests
  const [httpRefreshTrigger, setHttpRefreshTrigger] = useState(0)

  // Charger l'enquete
  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    loadInvestigation()
    loadFiles()
    loadScans()
    loadEnumScans()
  }, [id, user])

  // Polling pour le scan en cours
  useEffect(() => {
    if (activeScan && activeScan.status === 'running') {
      const interval = setInterval(() => {
        checkScanStatus(activeScan.id)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeScan])

  // Polling pour le scan d'enum en cours
  useEffect(() => {
    if (activeEnumScan && activeEnumScan.status === 'running') {
      const interval = setInterval(() => {
        checkEnumScanStatus(activeEnumScan.id)
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeEnumScan])

  const loadInvestigation = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setInvestigation(data)
      } else {
        navigate('/investigations')
      }
    } catch (error) {
      console.error('Erreur chargement:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadFiles = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}/files`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setFiles(data)
      }
    } catch (error) {
      console.error('Erreur chargement fichiers:', error)
    }
  }

  const loadScans = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}/scans`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setScans(data)

        // Charger les resultats du dernier scan complete
        const lastCompleted = data.find((s: ReconScan) => s.status === 'completed')
        if (lastCompleted) {
          loadScanResults(lastCompleted.id)
        }

        // Si un scan est en cours, le suivre
        const running = data.find((s: ReconScan) => s.status === 'running')
        if (running) {
          setActiveScan(running)
        }
      }
    } catch (error) {
      console.error('Erreur chargement scans:', error)
    }
  }

  const loadScanResults = async (scanId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/scans/${scanId}/results`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setReconResults(data.results)
      }
    } catch (error) {
      console.error('Erreur chargement resultats:', error)
    }
  }

  const checkScanStatus = async (scanId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/scans/${scanId}`, {
        credentials: 'include'
      })
      if (response.ok) {
        const scan = await response.json()
        if (scan.status === 'completed') {
          setActiveScan(null)
          loadScans()
          loadScanResults(scanId)
        } else if (scan.status === 'failed') {
          setActiveScan(null)
          loadScans()
        } else if (scan.status === 'running') {
          setActiveScan(scan)
        }
      }
    } catch (error) {
      console.error('Erreur verification scan:', error)
    }
  }

  // Lancer le scan avec la config avancee
  const startScan = async () => {
    setScanLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}/scans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          scan_mode: scanConfig.mode,
          tool: scanConfig.tool,
          wordlist: scanConfig.wordlist,
          custom_wordlist: scanConfig.customWordlist,
          threads: scanConfig.threads,
          extensions: scanConfig.extensions,
          user_agent: scanConfig.userAgent,
          cookies: scanConfig.cookies,
          custom_headers: scanConfig.customHeaders,
          timeout: scanConfig.timeout,
          follow_redirects: scanConfig.followRedirects,
          custom_flags: scanConfig.customFlags
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
      setScanLoading(false)
    }
  }

  // Enumeration functions
  const loadEnumScans = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}/enum`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setEnumScans(data)

        // Charger les resultats du dernier scan complete
        const lastCompleted = data.find((s: EnumScan) => s.status === 'completed')
        if (lastCompleted) {
          loadEnumResults(lastCompleted.id)
        }

        // Si un scan est en cours, le suivre
        const running = data.find((s: EnumScan) => s.status === 'running')
        if (running) {
          setActiveEnumScan(running)
        }
      }
    } catch (error) {
      console.error('Erreur chargement enum scans:', error)
    }
  }

  const loadEnumResults = async (scanId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/enum/${scanId}/results`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setEnumResults(data.results)
      }
    } catch (error) {
      console.error('Erreur chargement enum resultats:', error)
    }
  }

  const checkEnumScanStatus = async (scanId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/enum/${scanId}`, {
        credentials: 'include'
      })
      if (response.ok) {
        const scan = await response.json()
        if (scan.status === 'completed') {
          setActiveEnumScan(null)
          loadEnumScans()
          loadEnumResults(scanId)
        } else if (scan.status === 'failed') {
          setActiveEnumScan(null)
          loadEnumScans()
        } else if (scan.status === 'running') {
          setActiveEnumScan(scan)
        }
      }
    } catch (error) {
      console.error('Erreur verification enum scan:', error)
    }
  }

  const startEnumScan = async () => {
    setEnumLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}/enum`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      })

      if (response.ok) {
        const scan = await response.json()
        setActiveEnumScan(scan)
        loadEnumScans()
      }
    } catch (error) {
      console.error('Erreur lancement enum scan:', error)
    } finally {
      setEnumLoading(false)
    }
  }

  // Gestion de la selection d'un noeud
  const handleNodeSelect = useCallback((result: ReconResult | null) => {
    setSelectedNode(result)
  }, [])

  // Gestion de l'export de l'image
  const handleExportImage = useCallback(async (imageBlob: Blob) => {
    const formData = new FormData()
    const filename = `recon-graph-${new Date().toISOString().split('T')[0]}.png`
    formData.append('file', imageBlob, filename)

    try {
      const response = await fetch(`${API_URL}/api/investigations/${id}/files`, {
        method: 'POST',
        credentials: 'include',
        body: formData
      })

      if (response.ok) {
        loadFiles()
        setShowFilesPanel(true)
      }
    } catch (error) {
      console.error('Erreur sauvegarde image:', error)
    }
  }, [id])

  // Ouvrir le path dans le navigateur
  const openInBrowser = useCallback(() => {
    if (selectedNode && investigation) {
      const fullUrl = investigation.target_url.replace(/\/$/, '') + selectedNode.path
      window.open(fullUrl, '_blank')
    }
  }, [selectedNode, investigation])

  // Ouvrir un fichier pour visualisation
  const openFile = async (file: FileData) => {
    setSelectedFile(file)
    setRenameValue(file.original_filename)
    setFileContent(null)

    // Charger le contenu si c'est un fichier texte
    if (isTextFile(file.file_type)) {
      try {
        const response = await fetch(`${API_URL}/api/files/${file.id}/content`, {
          credentials: 'include'
        })
        if (response.ok) {
          const text = await response.text()
          setFileContent(text)
        }
      } catch (error) {
        console.error('Erreur chargement contenu:', error)
      }
    }

    setShowFileModal(true)
  }

  // Telecharger un fichier
  const downloadFile = (file: FileData) => {
    window.open(`${API_URL}/api/files/${file.id}/download`, '_blank')
  }

  // Renommer un fichier
  const renameFile = async () => {
    if (!selectedFile || !renameValue.trim()) return

    setIsRenaming(true)
    try {
      const response = await fetch(`${API_URL}/api/files/${selectedFile.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ original_filename: renameValue.trim() })
      })

      if (response.ok) {
        loadFiles()
        setSelectedFile({ ...selectedFile, original_filename: renameValue.trim() })
      }
    } catch (error) {
      console.error('Erreur renommage:', error)
    } finally {
      setIsRenaming(false)
    }
  }

  // Supprimer un fichier
  const deleteFile = async (file: FileData) => {
    if (!confirm(`Supprimer "${file.original_filename}" ?`)) return

    try {
      const response = await fetch(`${API_URL}/api/files/${file.id}`, {
        method: 'DELETE',
        credentials: 'include'
      })

      if (response.ok) {
        loadFiles()
        if (selectedFile?.id === file.id) {
          setShowFileModal(false)
          setSelectedFile(null)
        }
      }
    } catch (error) {
      console.error('Erreur suppression:', error)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  // Mettre a jour la config de scan
  const updateScanConfig = (key: keyof ScanConfig, value: any) => {
    setScanConfig(prev => ({ ...prev, [key]: value }))
  }

  // Rendu du contenu selon l'onglet actif
  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return (
          <div className="tab-content">
            <div className="info-grid">
              <div className="info-item">
                <label>URL cible</label>
                <a href={investigation?.target_url} target="_blank" rel="noopener noreferrer">
                  {investigation?.target_url}
                </a>
              </div>
              <div className="info-item">
                <label>Description</label>
                <p>{investigation?.description || 'Aucune description'}</p>
              </div>
              <div className="info-item">
                <label>Proprietaire</label>
                <p>{investigation?.owner.username}</p>
              </div>
              <div className="info-item">
                <label>Cree le</label>
                <p>{investigation?.created_at ? new Date(investigation.created_at).toLocaleDateString() : '-'}</p>
              </div>
            </div>
          </div>
        )

      case 'recon':
        return (
          <div className="tab-content recon-tab">
            <div className="recon-header">
              <h3>Arborescence du site</h3>
              <div className="recon-header-actions">
                <div className="view-toggle">
                  <button
                    className={`view-toggle-btn ${reconView === 'graph' ? 'active' : ''}`}
                    onClick={() => setReconView('graph')}
                  >
                    Graphe
                  </button>
                  <button
                    className={`view-toggle-btn ${reconView === 'list' ? 'active' : ''}`}
                    onClick={() => setReconView('list')}
                  >
                    Liste
                  </button>
                </div>
                <button
                  className="btn btn-primary"
                  onClick={() => setShowScanModal(true)}
                  disabled={activeScan !== null}
                >
                  {activeScan ? 'Scan en cours...' : 'Lancer un scan'}
                </button>
              </div>
            </div>

            {activeScan && (
              <div className="scan-progress">
                <span className="progress-spinner"></span>
                <span>
                  Scan en cours ({activeScan.scan_mode}) - {activeScan.progress_current || 0} / {activeScan.progress_total || 0} paths
                </span>
                {activeScan.progress_total > 0 && (
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${((activeScan.progress_current || 0) / activeScan.progress_total) * 100}%` }}
                    />
                  </div>
                )}
              </div>
            )}

            {reconView === 'graph' ? (
              <ReconGraph
                results={reconResults}
                onNodeSelect={handleNodeSelect}
                onExportImage={handleExportImage}
              />
            ) : (
              <ReconList
                results={reconResults}
                onResultSelect={handleNodeSelect}
              />
            )}

            {/* Panel de details du noeud selectionne */}
            {selectedNode && (
              <div className="node-details-panel">
                <div className="node-details-header">
                  <span className="node-details-path">{selectedNode.path}</span>
                  <button className="node-details-close" onClick={() => setSelectedNode(null)}>
                    x
                  </button>
                </div>

                <div className="node-details-grid">
                  <div className="detail-item">
                    <span className="detail-label">Status</span>
                    <span className={`status-badge ${getStatusClass(selectedNode.status_code)}`}>
                      {selectedNode.status_code || '-'} {getStatusText(selectedNode.status_code)}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Content-Type</span>
                    <span className="detail-value mono">{selectedNode.content_type || '-'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Content-Length</span>
                    <span className="detail-value">{selectedNode.content_length ? `${selectedNode.content_length} bytes` : '-'}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Parent</span>
                    <span className="detail-value mono">{selectedNode.parent_path || '(racine)'}</span>
                  </div>
                </div>

                <div className="node-details-actions">
                  <button className="action-btn" onClick={openInBrowser}>
                    Ouvrir dans le navigateur
                  </button>
                </div>
              </div>
            )}

            {scans.length > 0 && (
              <div className="scans-history">
                <h4>Historique des scans</h4>
                <ul className="scans-list">
                  {scans.slice(0, 5).map(scan => (
                    <li
                      key={scan.id}
                      className={`scan-item ${scan.status}`}
                      onClick={() => scan.status === 'completed' && loadScanResults(scan.id)}
                    >
                      <span className="scan-mode">{scan.scan_mode}</span>
                      <span className="scan-status">{scan.status}</span>
                      <span className="scan-count">{scan.results_count} paths</span>
                      <span className="scan-date">
                        {new Date(scan.created_at).toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )

      case 'enum':
        return (
          <div className="tab-content enum-tab">
            <div className="enum-header">
              <h3>Technologies & Headers HTTP</h3>
              <button
                className="btn btn-primary"
                onClick={startEnumScan}
                disabled={activeEnumScan !== null || enumLoading}
              >
                {activeEnumScan ? 'Scan en cours...' : enumLoading ? 'Lancement...' : 'Lancer l\'analyse'}
              </button>
            </div>

            {activeEnumScan && (
              <div className="scan-progress">
                <span className="progress-spinner"></span>
                <span>Analyse en cours...</span>
              </div>
            )}

            <EnumDisplay results={enumResults} />

            {enumScans.length > 0 && (
              <div className="scans-history">
                <h4>Historique des analyses</h4>
                <ul className="scans-list">
                  {enumScans.slice(0, 5).map(scan => (
                    <li
                      key={scan.id}
                      className={`scan-item ${scan.status}`}
                      onClick={() => scan.status === 'completed' && loadEnumResults(scan.id)}
                    >
                      <span className="scan-mode">Enum</span>
                      <span className="scan-status">{scan.status}</span>
                      <span className="scan-count">{scan.results_count} resultats</span>
                      <span className="scan-date">
                        {new Date(scan.created_at).toLocaleString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )

      case 'exploit':
        return (
          <div className="tab-content">
            <div className="exploit-container">
              <VulnDisplay investigationId={investigation.id} />

              <div className="http-tools-section">
                <h3 className="tools-section-title">HTTP Request Builder</h3>
                <RequestBuilder
                  investigationId={investigation.id}
                  onRequestSent={() => setHttpRefreshTrigger(prev => prev + 1)}
                />
                <HttpHistory
                  investigationId={investigation.id}
                  refreshTrigger={httpRefreshTrigger}
                />
              </div>
            </div>
          </div>
        )

      case 'rapport':
        return (
          <div className="tab-content">
            <div className="placeholder">
              <h3>Rapport de pentest</h3>
              <p>Synthese, vulnerabilites detectees, notes et export</p>
              <p className="hint">Dashboard, score de securite, timeline, export PDF...</p>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (loading) {
    return <div className="loading">Chargement...</div>
  }

  if (!investigation) {
    return <div className="loading">Enquete non trouvee</div>
  }

  return (
    <div className="investigation-page">
      {/* Header */}
      <header className="page-header">
        <div className="header-left">
          <span className="brand-name" onClick={() => navigate('/')}>BurpKiller</span>
          <span className="separator">/</span>
          <span className="breadcrumb" onClick={() => navigate('/investigations')}>Enquetes</span>
          <span className="separator">/</span>
          <span className="current">{investigation.name}</span>
        </div>
        <nav className="header-nav">
          <span className="user-name">{user?.username}</span>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </header>

      {/* Tabs */}
      <div className="tabs-container">
        <div className="tabs">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="page-content">
        {renderTabContent()}
      </main>

      {/* Modal scan avancee */}
      {showScanModal && (
        <div className="modal-overlay" onClick={() => setShowScanModal(false)}>
          <div className="modal modal-large" onClick={e => e.stopPropagation()}>
            <h2>Configuration du scan</h2>
            <p className="modal-subtitle">Cible: {investigation.target_url}</p>

            {/* Outil de scan */}
            <div className="form-group">
              <label>Outil</label>
              <div className="radio-group horizontal">
                <label className="radio-label compact">
                  <input
                    type="radio"
                    name="tool"
                    value="builtin"
                    checked={scanConfig.tool === 'builtin'}
                    onChange={e => updateScanConfig('tool', e.target.value)}
                  />
                  <span>Builtin (Python)</span>
                </label>
                <label className="radio-label compact">
                  <input
                    type="radio"
                    name="tool"
                    value="gobuster"
                    checked={scanConfig.tool === 'gobuster'}
                    onChange={e => updateScanConfig('tool', e.target.value)}
                  />
                  <span>Gobuster</span>
                </label>
                <label className="radio-label compact">
                  <input
                    type="radio"
                    name="tool"
                    value="feroxbuster"
                    checked={scanConfig.tool === 'feroxbuster'}
                    onChange={e => updateScanConfig('tool', e.target.value)}
                  />
                  <span>Feroxbuster</span>
                </label>
              </div>
            </div>

            {/* Mode de scan */}
            <div className="form-group">
              <label>Mode</label>
              <div className="radio-group horizontal">
                <label className="radio-label compact">
                  <input
                    type="radio"
                    name="mode"
                    value="stealth"
                    checked={scanConfig.mode === 'stealth'}
                    onChange={e => updateScanConfig('mode', e.target.value)}
                  />
                  <span>Discret (1 req/s)</span>
                </label>
                <label className="radio-label compact">
                  <input
                    type="radio"
                    name="mode"
                    value="normal"
                    checked={scanConfig.mode === 'normal'}
                    onChange={e => updateScanConfig('mode', e.target.value)}
                  />
                  <span>Normal (5 req/s)</span>
                </label>
                <label className="radio-label compact">
                  <input
                    type="radio"
                    name="mode"
                    value="aggressive"
                    checked={scanConfig.mode === 'aggressive'}
                    onChange={e => updateScanConfig('mode', e.target.value)}
                  />
                  <span>Agressif (20 req/s)</span>
                </label>
              </div>
            </div>

            {/* Wordlist */}
            <div className="form-group">
              <label>Wordlist</label>
              <select
                value={scanConfig.wordlist}
                onChange={e => updateScanConfig('wordlist', e.target.value)}
              >
                <option value="common">Common (~50 paths)</option>
                <option value="medium">Medium (~500 paths)</option>
                <option value="large">Large (~5000 paths)</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            {scanConfig.wordlist === 'custom' && (
              <div className="form-group">
                <label>Chemin wordlist custom</label>
                <input
                  type="text"
                  value={scanConfig.customWordlist}
                  onChange={e => updateScanConfig('customWordlist', e.target.value)}
                  placeholder="/path/to/wordlist.txt"
                />
              </div>
            )}

            {/* Options avancees */}
            <div className="form-group">
              <button
                type="button"
                className="toggle-advanced"
                onClick={() => setShowAdvancedScan(!showAdvancedScan)}
              >
                {showAdvancedScan ? '- Masquer' : '+ Afficher'} options avancees
              </button>
            </div>

            {showAdvancedScan && (
              <div className="advanced-options">
                <div className="form-row">
                  <div className="form-group half">
                    <label>Threads</label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={scanConfig.threads}
                      onChange={e => updateScanConfig('threads', parseInt(e.target.value) || 10)}
                    />
                  </div>
                  <div className="form-group half">
                    <label>Timeout (s)</label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      value={scanConfig.timeout}
                      onChange={e => updateScanConfig('timeout', parseInt(e.target.value) || 10)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Extensions (ex: php,html,js)</label>
                  <input
                    type="text"
                    value={scanConfig.extensions}
                    onChange={e => updateScanConfig('extensions', e.target.value)}
                    placeholder="php,html,js,txt"
                  />
                </div>

                <div className="form-group">
                  <label>User-Agent</label>
                  <input
                    type="text"
                    value={scanConfig.userAgent}
                    onChange={e => updateScanConfig('userAgent', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Cookies</label>
                  <input
                    type="text"
                    value={scanConfig.cookies}
                    onChange={e => updateScanConfig('cookies', e.target.value)}
                    placeholder="session=abc123; token=xyz"
                  />
                </div>

                <div className="form-group">
                  <label>Headers custom (un par ligne)</label>
                  <textarea
                    value={scanConfig.customHeaders}
                    onChange={e => updateScanConfig('customHeaders', e.target.value)}
                    placeholder="Authorization: Bearer token&#10;X-Custom: value"
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={scanConfig.followRedirects}
                      onChange={e => updateScanConfig('followRedirects', e.target.checked)}
                    />
                    Suivre les redirections
                  </label>
                </div>

                {(scanConfig.tool === 'gobuster' || scanConfig.tool === 'feroxbuster') && (
                  <div className="form-group">
                    <label>Flags custom</label>
                    <input
                      type="text"
                      value={scanConfig.customFlags}
                      onChange={e => updateScanConfig('customFlags', e.target.value)}
                      placeholder="--no-error --quiet"
                    />
                  </div>
                )}
              </div>
            )}

            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowScanModal(false)}
              >
                Annuler
              </button>
              <button
                className="btn btn-primary"
                onClick={startScan}
                disabled={scanLoading}
              >
                {scanLoading ? 'Lancement...' : 'Lancer le scan'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal fichier */}
      {showFileModal && selectedFile && (
        <div className="modal-overlay" onClick={() => setShowFileModal(false)}>
          <div className="modal modal-file" onClick={e => e.stopPropagation()}>
            <div className="file-modal-header">
              <div className="file-modal-title">
                {isRenaming ? (
                  <input
                    type="text"
                    value={renameValue}
                    onChange={e => setRenameValue(e.target.value)}
                    onBlur={renameFile}
                    onKeyDown={e => e.key === 'Enter' && renameFile()}
                    autoFocus
                  />
                ) : (
                  <span onClick={() => setIsRenaming(true)}>{selectedFile.original_filename}</span>
                )}
              </div>
              <button className="modal-close" onClick={() => setShowFileModal(false)}>x</button>
            </div>

            <div className="file-modal-info">
              <span>Type: {selectedFile.file_type.toUpperCase()}</span>
              <span>Taille: {formatFileSize(selectedFile.file_size || 0)}</span>
              <span>Par: {selectedFile.uploaded_by.username}</span>
              <span>Le: {new Date(selectedFile.created_at).toLocaleString()}</span>
            </div>

            <div className="file-modal-content">
              {isImageFile(selectedFile.file_type) ? (
                <img
                  src={`${API_URL}/api/files/${selectedFile.id}/download`}
                  alt={selectedFile.original_filename}
                  className="file-preview-image"
                />
              ) : isTextFile(selectedFile.file_type) ? (
                <pre className="file-preview-text">
                  {fileContent || 'Chargement...'}
                </pre>
              ) : (
                <div className="file-preview-unsupported">
                  <p>Apercu non disponible pour ce type de fichier</p>
                  <p className="hint">Utilisez le bouton Telecharger pour voir le contenu</p>
                </div>
              )}
            </div>

            <div className="file-modal-actions">
              <button className="btn btn-secondary" onClick={() => setIsRenaming(true)}>
                Renommer
              </button>
              <button className="btn btn-secondary" onClick={() => downloadFile(selectedFile)}>
                Telecharger
              </button>
              <button className="btn btn-danger" onClick={() => deleteFile(selectedFile)}>
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bouton flottant fichiers */}
      <div className="fab-container">
        <button
          className={`fab ${showFilesPanel ? 'active' : ''}`}
          onClick={() => setShowFilesPanel(!showFilesPanel)}
        >
          <span className="fab-icon">F</span>
          <span className="fab-badge">{files.length}</span>
        </button>

        {showFilesPanel && (
          <div className="files-panel">
            <div className="files-header">
              <h3>Fichiers partages</h3>
              <button className="close-btn" onClick={() => setShowFilesPanel(false)}>X</button>
            </div>
            {files.length === 0 ? (
              <p className="no-files">Aucun fichier partage</p>
            ) : (
              <ul className="files-list">
                {files.map(file => (
                  <li key={file.id} className="file-item">
                    <div className="file-item-main" onClick={() => openFile(file)}>
                      <span className="file-name">{file.original_filename}</span>
                      <span className="file-meta">
                        {formatFileSize(file.file_size || 0)} - {file.uploaded_by.username}
                      </span>
                    </div>
                    <div className="file-item-actions">
                      <button
                        className="file-action-btn"
                        onClick={e => { e.stopPropagation(); downloadFile(file); }}
                        title="Telecharger"
                      >
                        DL
                      </button>
                      <button
                        className="file-action-btn danger"
                        onClick={e => { e.stopPropagation(); deleteFile(file); }}
                        title="Supprimer"
                      >
                        X
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Investigation

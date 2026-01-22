import { useState, useEffect } from 'react'
import './NetworkDisplay.css'

interface NetworkScan {
  id: number
  target: string
  scan_type: string
  scan_mode: string
  status: string
  progress_current: number
  progress_total: number
  results_count: number
  created_at: string
  completed_at: string | null
  error_message: string | null
}

interface NetworkResult {
  id: number
  ip: string
  hostname: string | null
  port: number | null
  protocol: string
  state: string
  service: string | null
  banner: string | null
}

interface NetworkDisplayProps {
  investigationId: number
  targetHost?: string
}

function NetworkDisplay({ investigationId, targetHost }: NetworkDisplayProps) {
  const [scans, setScans] = useState<NetworkScan[]>([])
  const [results, setResults] = useState<NetworkResult[]>([])
  const [activeScan, setActiveScan] = useState<NetworkScan | null>(null)
  const [loading, setLoading] = useState(false)
  const [showScanModal, setShowScanModal] = useState(false)

  // Config du scan
  const [scanTarget, setScanTarget] = useState(targetHost || '')
  const [scanType, setScanType] = useState<'quick' | 'full' | 'all'>('quick')
  const [scanMode, setScanMode] = useState<'portscan' | 'pingsweep'>('portscan')

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
      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/network-scans`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setScans(data)

        const lastCompleted = data.find((s: NetworkScan) => s.status === 'completed')
        if (lastCompleted) {
          loadResults(lastCompleted.id)
        }

        const running = data.find((s: NetworkScan) => s.status === 'running')
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
      const response = await fetch(`${API_URL}/api/network-scans/${scanId}/results`, {
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
      const response = await fetch(`${API_URL}/api/network-scans/${scanId}`, {
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

  const startScan = async () => {
    if (!scanTarget) return

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/investigations/${investigationId}/network-scans`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          target: scanTarget,
          scan_type: scanType,
          scan_mode: scanMode
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

  const getServiceClass = (service: string | null): string => {
    if (!service) return ''
    const s = service.toLowerCase()
    if (['ssh', 'rdp', 'vnc', 'telnet'].includes(s)) return 'remote-access'
    if (['http', 'https', 'http-proxy'].includes(s)) return 'web'
    if (['mysql', 'postgresql', 'mssql', 'oracle', 'mongodb', 'redis'].includes(s)) return 'database'
    if (['smb', 'ftp', 'nfs'].includes(s)) return 'file-share'
    if (['ldap', 'ldaps', 'kerberos'].includes(s)) return 'directory'
    if (['smtp', 'pop3', 'imap'].includes(s)) return 'mail'
    return ''
  }

  const groupedResults = results.reduce((acc, r) => {
    const key = r.ip
    if (!acc[key]) {
      acc[key] = { ip: r.ip, hostname: r.hostname, ports: [] }
    }
    if (r.port) {
      acc[key].ports.push(r)
    }
    return acc
  }, {} as Record<string, { ip: string; hostname: string | null; ports: NetworkResult[] }>)

  return (
    <div className="network-display">
      <div className="network-header">
        <h3>Scan Reseau</h3>
        <button
          className="btn btn-primary"
          onClick={() => setShowScanModal(true)}
          disabled={activeScan !== null}
        >
          {activeScan ? 'Scan en cours...' : 'Nouveau scan'}
        </button>
      </div>

      {activeScan && (
        <div className="scan-progress">
          <span className="progress-spinner"></span>
          <span>
            {activeScan.scan_mode === 'pingsweep' ? 'Ping sweep' : 'Port scan'} en cours sur {activeScan.target}
          </span>
          {activeScan.progress_total > 0 && (
            <div className="progress-bar">
              <div
                className="progress-bar-fill"
                style={{ width: `${(activeScan.progress_current / activeScan.progress_total) * 100}%` }}
              />
            </div>
          )}
          <span className="progress-text">
            {activeScan.progress_current} / {activeScan.progress_total}
          </span>
        </div>
      )}

      {Object.keys(groupedResults).length > 0 ? (
        <div className="network-results">
          <div className="results-summary">
            <span className="summary-item">
              <strong>{Object.keys(groupedResults).length}</strong> hote(s)
            </span>
            <span className="summary-item">
              <strong>{results.filter(r => r.port).length}</strong> port(s) ouvert(s)
            </span>
          </div>

          {Object.values(groupedResults).map(host => (
            <div key={host.ip} className="host-card">
              <div className="host-header">
                <span className="host-ip">{host.ip}</span>
                {host.hostname && <span className="host-name">{host.hostname}</span>}
                <span className="port-count">{host.ports.length} port(s)</span>
              </div>

              {host.ports.length > 0 && (
                <div className="ports-table">
                  <div className="ports-header">
                    <span>Port</span>
                    <span>Service</span>
                    <span>Banniere</span>
                  </div>
                  {host.ports.map(port => (
                    <div key={port.id} className={`port-row ${getServiceClass(port.service)}`}>
                      <span className="port-number">
                        {port.port}/{port.protocol}
                      </span>
                      <span className="port-service">{port.service || 'Unknown'}</span>
                      <span className="port-banner" title={port.banner || ''}>
                        {port.banner ? port.banner.substring(0, 80) + (port.banner.length > 80 ? '...' : '') : '-'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="no-results">
          <p>Aucun resultat de scan reseau</p>
          <p className="hint">Lancez un scan pour decouvrir les ports ouverts</p>
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
                onClick={() => scan.status === 'completed' && loadResults(scan.id)}
              >
                <span className="scan-target">{scan.target}</span>
                <span className="scan-mode">{scan.scan_mode}</span>
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
            <h2>Nouveau scan reseau</h2>

            <div className="form-group">
              <label>Cible (IP, hostname ou CIDR)</label>
              <input
                type="text"
                value={scanTarget}
                onChange={e => setScanTarget(e.target.value)}
                placeholder="192.168.1.1 ou 192.168.1.0/24"
              />
            </div>

            <div className="form-group">
              <label>Mode</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="scanMode"
                    value="portscan"
                    checked={scanMode === 'portscan'}
                    onChange={() => setScanMode('portscan')}
                  />
                  <span>Scan de ports</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="scanMode"
                    value="pingsweep"
                    checked={scanMode === 'pingsweep'}
                    onChange={() => setScanMode('pingsweep')}
                  />
                  <span>Ping sweep (decouverte d'hotes)</span>
                </label>
              </div>
            </div>

            {scanMode === 'portscan' && (
              <div className="form-group">
                <label>Type de scan</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="scanType"
                      value="quick"
                      checked={scanType === 'quick'}
                      onChange={() => setScanType('quick')}
                    />
                    <span>Quick (~25 ports communs)</span>
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="scanType"
                      value="full"
                      checked={scanType === 'full'}
                      onChange={() => setScanType('full')}
                    />
                    <span>Full (~100 ports)</span>
                  </label>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="scanType"
                      value="all"
                      checked={scanType === 'all'}
                      onChange={() => setScanType('all')}
                    />
                    <span>All (1-65535)</span>
                  </label>
                </div>
              </div>
            )}

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

export default NetworkDisplay

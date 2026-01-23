import { useEffect, useState } from 'react'
import './Processes.css'

interface Process {
  id: string
  type: string
  description: string
  owner: string
  started_at: number
  status: string
  message?: string
}

export default function Processes() {
  const [procs, setProcs] = useState<Process[]>([])
  const [loading, setLoading] = useState(true)

  async function fetchProcs() {
    try {
      const res = await fetch('/api/processes', {
        credentials: 'include'
      })
      const json = await res.json()
      setProcs(json.processes || [])
    } catch (e) {
      console.error('Erreur chargement processus:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProcs()
    const interval = setInterval(fetchProcs, 3000)
    return () => clearInterval(interval)
  }, [])

  function getStatusClass(status: string): string {
    switch (status) {
      case 'running': return 'status-running'
      case 'completed':
      case 'stopped': return 'status-completed'
      case 'failed': return 'status-failed'
      default: return ''
    }
  }

  function formatTime(timestamp: number): string {
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString()
  }

  if (loading) {
    return (
      <div className="processes">
        <h5>Processus</h5>
        <p className="loading-text">Chargement...</p>
      </div>
    )
  }

  const runningCount = procs.filter(p => p.status === 'running').length

  return (
    <div className="processes">
      <h5>Processus ({runningCount} en cours)</h5>
      <ul className="processes-list">
        {procs.length === 0 && (
          <li className="no-processes">Aucun processus</li>
        )}
        {procs.map(p => (
          <li key={p.id} className={`process-item ${getStatusClass(p.status)}`}>
            <div className="process-main">
              <span className="process-type">{p.type}</span>
              <span className="process-desc">{p.description}</span>
            </div>
            <div className="process-meta">
              <span className="process-owner">par {p.owner}</span>
              <span className="process-time">{formatTime(p.started_at)}</span>
              <span className={`process-status ${getStatusClass(p.status)}`}>
                {p.status}
              </span>
            </div>
            {p.message && (
              <div className="process-message">{p.message}</div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

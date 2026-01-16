import { useState, useEffect } from 'react'
import './HttpHistory.css'

interface HttpRequestData {
  id: number
  method: string
  url: string
  headers: Record<string, string>
  body: string | null
  response_status: number | null
  response_headers: Record<string, string> | null
  response_body: string | null
  response_time: number | null
  error_message: string | null
  created_at: string
  sent_by: {
    id: number
    username: string
  }
}

interface HttpHistoryProps {
  investigationId: number
  refreshTrigger?: number
  onReplay?: (request: HttpRequestData) => void
}

function HttpHistory({ investigationId, refreshTrigger, onReplay }: HttpHistoryProps) {
  const [requests, setRequests] = useState<HttpRequestData[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedRequest, setSelectedRequest] = useState<HttpRequestData | null>(null)

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:5000/api/investigations/${investigationId}/http-requests`, {
        credentials: 'include'
      })
      if (res.ok) {
        const data = await res.json()
        setRequests(data)
      }
    } catch (error) {
      console.error('Erreur lors du chargement de l\'historique:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [investigationId, refreshTrigger])

  const handleDelete = async (requestId: number) => {
    if (!confirm('Supprimer cette requete de l\'historique ?')) {
      return
    }

    try {
      const res = await fetch(`http://localhost:5000/api/http-requests/${requestId}`, {
        method: 'DELETE',
        credentials: 'include'
      })

      if (res.ok) {
        setRequests(requests.filter(r => r.id !== requestId))
        if (selectedRequest?.id === requestId) {
          setSelectedRequest(null)
        }
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error)
      alert('Erreur lors de la suppression')
    }
  }

  const getStatusColorClass = (status: number | null): string => {
    if (!status) return ''
    if (status >= 200 && status < 300) return 'status-success'
    if (status >= 300 && status < 400) return 'status-redirect'
    if (status >= 400 && status < 500) return 'status-client-error'
    if (status >= 500) return 'status-server-error'
    return ''
  }

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr)
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading && requests.length === 0) {
    return (
      <div className="http-history">
        <div className="loading-state">Chargement de l'historique...</div>
      </div>
    )
  }

  if (requests.length === 0) {
    return (
      <div className="http-history">
        <div className="empty-state">
          <p>Aucune requete dans l'historique</p>
          <p className="hint">Utilisez le Request Builder pour envoyer des requetes HTTP</p>
        </div>
      </div>
    )
  }

  return (
    <div className="http-history">
      <div className="history-header">
        <h3 className="history-title">Historique HTTP ({requests.length})</h3>
        <button className="refresh-button" onClick={fetchHistory}>
          Actualiser
        </button>
      </div>

      <div className="history-content">
        {/* Liste des requetes */}
        <div className="requests-list">
          {requests.map(request => (
            <div
              key={request.id}
              className={`request-item ${selectedRequest?.id === request.id ? 'selected' : ''}`}
              onClick={() => setSelectedRequest(request)}
            >
              <div className="request-item-header">
                <span className={`method-badge method-${request.method.toLowerCase()}`}>
                  {request.method}
                </span>
                {request.response_status && (
                  <span className={`status-indicator ${getStatusColorClass(request.response_status)}`}>
                    {request.response_status}
                  </span>
                )}
                {request.error_message && (
                  <span className="status-indicator status-error">Error</span>
                )}
              </div>

              <div className="request-item-url">{request.url}</div>

              <div className="request-item-footer">
                <span className="request-date">{formatDate(request.created_at)}</span>
                {request.response_time !== null && (
                  <span className="request-time">{(request.response_time * 1000).toFixed(0)}ms</span>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Details de la requete selectionnee */}
        {selectedRequest && (
          <div className="request-details">
            <div className="details-header">
              <h4 className="details-title">Details de la requete</h4>
              <div className="details-actions">
                {onReplay && (
                  <button
                    className="replay-button"
                    onClick={() => onReplay(selectedRequest)}
                  >
                    Rejouer
                  </button>
                )}
                <button
                  className="delete-button"
                  onClick={() => handleDelete(selectedRequest.id)}
                >
                  Supprimer
                </button>
              </div>
            </div>

            {/* Request info */}
            <div className="details-section">
              <div className="details-label">Methode et URL</div>
              <div className="details-request-line">
                <span className={`method-badge method-${selectedRequest.method.toLowerCase()}`}>
                  {selectedRequest.method}
                </span>
                <code className="details-url">{selectedRequest.url}</code>
              </div>
            </div>

            {/* Request Headers */}
            {selectedRequest.headers && Object.keys(selectedRequest.headers).length > 0 && (
              <div className="details-section">
                <div className="details-label">Request Headers</div>
                <div className="headers-display">
                  {Object.entries(selectedRequest.headers).map(([key, value]) => (
                    <div key={key} className="header-display-row">
                      <code className="header-key">{key}:</code>
                      <code className="header-value">{value}</code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Request Body */}
            {selectedRequest.body && (
              <div className="details-section">
                <div className="details-label">Request Body</div>
                <pre className="body-content">{selectedRequest.body}</pre>
              </div>
            )}

            {/* Response */}
            {selectedRequest.error_message ? (
              <div className="details-section">
                <div className="details-label">Error</div>
                <div className="error-display">{selectedRequest.error_message}</div>
              </div>
            ) : (
              <>
                {/* Response Status */}
                <div className="details-section">
                  <div className="details-label">Response</div>
                  <div className="response-summary">
                    <span className={`status-badge ${getStatusColorClass(selectedRequest.response_status)}`}>
                      Status: {selectedRequest.response_status}
                    </span>
                    {selectedRequest.response_time !== null && (
                      <span className="time-badge">
                        Time: {(selectedRequest.response_time * 1000).toFixed(0)}ms
                      </span>
                    )}
                  </div>
                </div>

                {/* Response Headers */}
                {selectedRequest.response_headers && Object.keys(selectedRequest.response_headers).length > 0 && (
                  <div className="details-section">
                    <div className="details-label">Response Headers</div>
                    <div className="headers-display">
                      {Object.entries(selectedRequest.response_headers).map(([key, value]) => (
                        <div key={key} className="header-display-row">
                          <code className="header-key">{key}:</code>
                          <code className="header-value">{value}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Response Body */}
                {selectedRequest.response_body && (
                  <div className="details-section">
                    <div className="details-label">Response Body</div>
                    <pre className="body-content">{selectedRequest.response_body}</pre>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default HttpHistory

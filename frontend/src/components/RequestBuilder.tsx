import { useState } from 'react'
import './RequestBuilder.css'

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
}

interface RequestBuilderProps {
  investigationId: number
  onRequestSent?: (request: HttpRequestData) => void
}

function RequestBuilder({ investigationId, onRequestSent }: RequestBuilderProps) {
  const [method, setMethod] = useState('GET')
  const [url, setUrl] = useState('')
  const [headers, setHeaders] = useState<Array<{ key: string; value: string }>>([
    { key: '', value: '' }
  ])
  const [body, setBody] = useState('')
  const [followRedirects, setFollowRedirects] = useState(true)
  const [verifySSL, setVerifySSL] = useState(true)

  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<HttpRequestData | null>(null)

  const handleAddHeader = () => {
    setHeaders([...headers, { key: '', value: '' }])
  }

  const handleRemoveHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index))
  }

  const handleHeaderChange = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...headers]
    newHeaders[index][field] = value
    setHeaders(newHeaders)
  }

  const handleSendRequest = async () => {
    if (!url) {
      alert('URL requise')
      return
    }

    setLoading(true)
    setResponse(null)

    try {
      // Convertir headers en objet
      const headersObj: Record<string, string> = {}
      headers.forEach(h => {
        if (h.key && h.value) {
          headersObj[h.key] = h.value
        }
      })

      const res = await fetch(`http://localhost:5000/api/investigations/${investigationId}/http-requests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          method,
          url,
          headers: headersObj,
          body: body || null,
          followRedirects,
          verifySSL
        })
      })

      const data = await res.json()
      setResponse(data)

      if (onRequestSent) {
        onRequestSent(data)
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi de la requete:', error)
      alert('Erreur lors de l\'envoi de la requete')
    } finally {
      setLoading(false)
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

  return (
    <div className="request-builder">
      <div className="request-section">
        <h3 className="section-title">Request Builder</h3>

        {/* Method + URL */}
        <div className="request-line">
          <select
            className="method-select"
            value={method}
            onChange={(e) => setMethod(e.target.value)}
          >
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
            <option value="PATCH">PATCH</option>
            <option value="HEAD">HEAD</option>
            <option value="OPTIONS">OPTIONS</option>
          </select>

          <input
            type="text"
            className="url-input"
            placeholder="https://example.com/api/endpoint"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />

          <button
            className="send-button"
            onClick={handleSendRequest}
            disabled={loading || !url}
          >
            {loading ? 'Envoi...' : 'Send'}
          </button>
        </div>

        {/* Headers */}
        <div className="headers-section">
          <div className="subsection-header">
            <span className="subsection-title">Headers</span>
            <button className="add-header-button" onClick={handleAddHeader}>
              + Add Header
            </button>
          </div>

          <div className="headers-list">
            {headers.map((header, index) => (
              <div key={index} className="header-row">
                <input
                  type="text"
                  className="header-key"
                  placeholder="Header name"
                  value={header.key}
                  onChange={(e) => handleHeaderChange(index, 'key', e.target.value)}
                />
                <input
                  type="text"
                  className="header-value"
                  placeholder="Header value"
                  value={header.value}
                  onChange={(e) => handleHeaderChange(index, 'value', e.target.value)}
                />
                <button
                  className="remove-header-button"
                  onClick={() => handleRemoveHeader(index)}
                  disabled={headers.length === 1}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Body */}
        {['POST', 'PUT', 'PATCH'].includes(method) && (
          <div className="body-section">
            <span className="subsection-title">Body</span>
            <textarea
              className="body-textarea"
              placeholder="Request body (JSON, XML, etc.)"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={8}
            />
          </div>
        )}

        {/* Options */}
        <div className="options-section">
          <label className="option-label">
            <input
              type="checkbox"
              checked={followRedirects}
              onChange={(e) => setFollowRedirects(e.target.checked)}
            />
            Follow redirects
          </label>
          <label className="option-label">
            <input
              type="checkbox"
              checked={verifySSL}
              onChange={(e) => setVerifySSL(e.target.checked)}
            />
            Verify SSL certificate
          </label>
        </div>
      </div>

      {/* Response */}
      {response && (
        <div className="response-section">
          <h3 className="section-title">Response</h3>

          {response.error_message ? (
            <div className="response-error">
              <div className="error-title">Error</div>
              <div className="error-message">{response.error_message}</div>
            </div>
          ) : (
            <>
              {/* Status + Time */}
              <div className="response-summary">
                <span className={`status-badge ${getStatusColorClass(response.response_status)}`}>
                  Status: {response.response_status}
                </span>
                {response.response_time !== null && (
                  <span className="time-badge">
                    Time: {(response.response_time * 1000).toFixed(0)}ms
                  </span>
                )}
              </div>

              {/* Response Headers */}
              {response.response_headers && Object.keys(response.response_headers).length > 0 && (
                <div className="response-headers">
                  <span className="subsection-title">Response Headers</span>
                  <div className="headers-display">
                    {Object.entries(response.response_headers).map(([key, value]) => (
                      <div key={key} className="header-display-row">
                        <code className="header-display-key">{key}:</code>
                        <code className="header-display-value">{value}</code>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Response Body */}
              {response.response_body && (
                <div className="response-body">
                  <span className="subsection-title">Response Body</span>
                  <pre className="response-body-content">{response.response_body}</pre>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default RequestBuilder

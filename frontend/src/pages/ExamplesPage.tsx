import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './ExamplesPage.css'

interface Script {
  id: number;
  name: string;
  description: string;
  code: string;
  category?: string;
  filename?: string;
}

interface ExecuteResult {
  success: boolean;
  output?: string;
  error?: string;
  returncode?: number;
}

function ExamplesPage() {
  const navigate = useNavigate()
  const [scripts, setScripts] = useState<Script[]>([])
  const [selectedScript, setSelectedScript] = useState<Script | null>(null)
  const [output, setOutput] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)

  const API_URL = 'http://localhost:5000'

  useEffect(() => {
    loadExampleScripts()
  }, [])

  const loadExampleScripts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/scripts`)
      if (response.ok) {
        const data = await response.json()
        setScripts(data)
      }
    } catch (err) {
      console.error('Error loading scripts:', err)
    }
  }

  const executeScript = async (script: Script) => {
    setLoading(true)
    setOutput('')
    setError('')
    setSelectedScript(script)

    try {
      const response = await fetch(`${API_URL}/api/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: script.code }),
      })

      const data: ExecuteResult = await response.json()

      if (data.success) {
        setOutput(data.output || '')
        if (data.error) {
          setError(data.error)
        }
      } else {
        setError(data.error || 'Unknown error')
      }
    } catch (err) {
      setError(`Backend connection error: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  // Group scripts by category
  const groupedScripts = scripts.reduce((acc, script) => {
    const category = script.category || 'Other'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(script)
    return acc
  }, {} as Record<string, Script[]>)

  return (
    <div className="examples-page">
      <header className="examples-header">
        <button className="btn-back" onClick={() => navigate('/')}>
          Back
        </button>
        <h1>Example Scripts</h1>
        <div></div>
      </header>

      <div className="examples-container">
        <div className="scripts-sidebar">
          <div className="sidebar-header">
            <h2>Scripts</h2>
            <span className="script-count">{scripts.length}</span>
          </div>
          <div className="scripts-list">
            {Object.entries(groupedScripts).map(([category, categoryScripts]) => (
              <div key={category} className="category-group">
                <div className="category-title">{category}</div>
                {categoryScripts.map((script) => (
                  <div
                    key={script.id}
                    className={`script-item ${selectedScript?.id === script.id ? 'active' : ''}`}
                    onClick={() => setSelectedScript(script)}
                  >
                    <div className="script-name">{script.name}</div>
                    <div className="script-desc">{script.description}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="script-viewer">
          {selectedScript ? (
            <>
              <div className="viewer-header">
                <div>
                  <h2>{selectedScript.name}</h2>
                  <p>{selectedScript.description}</p>
                </div>
                <button
                  onClick={() => executeScript(selectedScript)}
                  disabled={loading}
                  className="btn-run"
                >
                  {loading ? 'Running...' : 'Run Script'}
                </button>
              </div>

              <div className="code-section">
                <div className="section-label">Code</div>
                <pre className="code-display">{selectedScript.code}</pre>
              </div>

              {(output || error) && (
                <div className="result-section">
                  <div className="section-label">Results</div>
                  {output && (
                    <div className="output-display">
                      <div className="result-label">Output:</div>
                      <pre>{output}</pre>
                    </div>
                  )}
                  {error && (
                    <div className="error-display">
                      <div className="result-label">Error:</div>
                      <pre>{error}</pre>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="viewer-placeholder">
              Select a script from the sidebar to view and run it
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ExamplesPage

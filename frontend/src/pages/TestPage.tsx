import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './TestPage.css'

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

function TestPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState<string>('print("Hello, World!")')
  const [output, setOutput] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [scripts, setScripts] = useState<Script[]>([])
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false)

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

  const executeCode = async () => {
    setLoading(true)
    setOutput('')
    setError('')

    try {
      const response = await fetch(`${API_URL}/api/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
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

  const clearEditor = () => {
    setCode('')
    setOutput('')
    setError('')
  }

  const loadScript = (script: Script) => {
    setCode(script.code)
    setOutput('')
    setError('')
    setDrawerOpen(false)
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
    <div className="test-page">
      <header className="test-header">
        <button className="btn-back" onClick={() => navigate('/')}>
          Back
        </button>
        <h1>Test Python Scripts</h1>
        <button className="btn-examples" onClick={() => setDrawerOpen(!drawerOpen)}>
          {drawerOpen ? 'Hide' : 'Examples'} ({scripts.length})
        </button>
      </header>

      {/* Drawer overlay */}
      {drawerOpen && (
        <div className="drawer-overlay" onClick={() => setDrawerOpen(false)}></div>
      )}

      {/* Drawer */}
      <div className={`drawer ${drawerOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <h2>Example Scripts</h2>
          <button className="drawer-close" onClick={() => setDrawerOpen(false)}>
            Close
          </button>
        </div>
        <div className="drawer-content">
          {Object.entries(groupedScripts).map(([category, categoryScripts]) => (
            <div key={category} className="drawer-category">
              <div className="drawer-category-title">{category}</div>
              {categoryScripts.map((script) => (
                <div
                  key={script.id}
                  className="drawer-script"
                  onClick={() => loadScript(script)}
                >
                  <div className="drawer-script-name">{script.name}</div>
                  <div className="drawer-script-desc">{script.description}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="test-container">
        <div className="editor-panel">
          <div className="panel-header">
            <h2>Editor</h2>
            <div className="editor-actions">
              <button onClick={clearEditor} className="btn-clear">
                Clear
              </button>
              <button 
                onClick={executeCode} 
                disabled={loading || !code.trim()}
                className="btn-execute"
              >
                {loading ? 'Running...' : 'Run'}
              </button>
            </div>
          </div>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter your Python code here..."
            className="code-editor"
            spellCheck={false}
          />
        </div>

        <div className="output-panel">
          <div className="panel-header">
            <h2>Output</h2>
          </div>
          <div className="output-content">
            {output && (
              <div className="output-section">
                <div className="output-label">Output:</div>
                <pre className="output-text">{output}</pre>
              </div>
            )}
            {error && (
              <div className="error-section">
                <div className="error-label">Error:</div>
                <pre className="error-text">{error}</pre>
              </div>
            )}
            {!output && !error && !loading && (
              <div className="output-placeholder">
                No output yet. Run your code to see results here.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TestPage

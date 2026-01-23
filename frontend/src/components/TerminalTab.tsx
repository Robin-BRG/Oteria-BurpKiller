import { useState } from 'react'
import './TerminalTab.css'

export default function TerminalTab() {
  const [code, setCode] = useState<string>("# Ecrire du code Python ici\nprint('Hello from Terminal')")
  const [output, setOutput] = useState<string>('')
  const [running, setRunning] = useState<boolean>(false)
  const [timeout, setTimeout] = useState<number>(10)

  async function runCode() {
    setRunning(true)
    setOutput('')

    try {
      const res = await fetch('/api/terminal/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code, timeout })
      })

      const json = await res.json()

      let out = ''
      if (json.stdout) {
        out += `${json.stdout}`
      }
      if (json.stderr) {
        out += `\n--- STDERR ---\n${json.stderr}`
      }
      out += `\n--- Return code: ${json.returncode} ---`

      if (json.timeout) {
        out += '\n[TIMEOUT]'
      }

      setOutput(out.trim())
    } catch (err: unknown) {
      setOutput(`Erreur: ${String(err)}`)
    } finally {
      setRunning(false)
    }
  }

  function clearOutput() {
    setOutput('')
  }

  function clearCode() {
    setCode('')
  }

  return (
    <div className="terminal-container">
      <div className="terminal-header">
        <h3>Terminal Python</h3>
        <div className="terminal-controls">
          <label className="timeout-label">
            Timeout:
            <input
              type="number"
              min="1"
              max="30"
              value={timeout}
              onChange={(e) => setTimeout(parseInt(e.target.value) || 10)}
              className="timeout-input"
            />
            s
          </label>
          <button
            onClick={runCode}
            disabled={running || !code.trim()}
            className="btn btn-primary"
          >
            {running ? 'Execution...' : 'Executer'}
          </button>
          <button onClick={clearCode} className="btn btn-secondary">
            Effacer code
          </button>
          <button onClick={clearOutput} className="btn btn-secondary">
            Effacer output
          </button>
        </div>
      </div>

      <div className="terminal-body">
        <div className="terminal-editor">
          <div className="terminal-section-header">Code</div>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="# Entrez votre code Python ici..."
            spellCheck={false}
            className="code-textarea"
          />
        </div>

        <div className="terminal-output">
          <div className="terminal-section-header">Output</div>
          <pre className="output-pre">
            {output || 'Aucune sortie'}
          </pre>
        </div>
      </div>

      <div className="terminal-warning">
        <strong>Attention:</strong> Ce terminal execute du code Python reel sur le serveur.
        Utilisez-le uniquement pour des scripts de test legitimes.
      </div>
    </div>
  )
}

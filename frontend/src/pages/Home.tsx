import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Home.css'

function Home() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [backendStatus, setBackendStatus] = useState<string>('Checking...')
  const API_URL = 'http://localhost:5000'

  useEffect(() => {
    checkBackendHealth()
  }, [])

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`)
      if (response.ok) {
        setBackendStatus('Connected')
      } else {
        setBackendStatus('Connection Error')
      }
    } catch (err) {
      setBackendStatus('Backend Unavailable')
    }
  }

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div className="home">
      <div className="home-container">
        <div className="home-header">
          <div className="header-left">
            <h1>Oteria Python</h1>
            <p className="home-subtitle">Python Script Executor</p>
          </div>
          <div className="header-right">
            {user ? (
              <div className="user-info">
                <span className="user-name">Hello, {user.username}</span>
                <button className="btn-logout" onClick={handleLogout}>Logout</button>
              </div>
            ) : (
              <div className="auth-buttons">
                <button className="btn-login" onClick={() => navigate('/login')}>Login</button>
                <button className="btn-register" onClick={() => navigate('/register')}>Register</button>
              </div>
            )}
          </div>
        </div>

        <div className="status-section">
          <div className="status-indicator">
            <span className={`status-dot ${backendStatus === 'Connected' ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">Backend: {backendStatus}</span>
          </div>
        </div>

        <div className="home-actions">
          <button className="btn-primary" onClick={() => navigate('/test')}>
            Test Scripts
          </button>
        </div>

        <div className="home-info">
          <div className="info-card">
            <h3>Execute Python Scripts</h3>
            <p>Run Python code directly from your browser with real-time results</p>
          </div>
          <div className="info-card">
            <h3>Example Library</h3>
            <p>Access example scripts from the side drawer in the Test page</p>
          </div>
          <div className="info-card">
            <h3>Custom Scripts</h3>
            <p>Write and test your own Python code with instant feedback</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home

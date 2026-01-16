import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Home.css'

function Home() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  // Status de connexion au backend
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking')
  const API_URL = ''

  // Verification du backend au chargement
  useEffect(() => {
    checkBackendHealth()
  }, [])

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`)
      if (response.ok) {
        setBackendStatus('connected')
      } else {
        setBackendStatus('error')
      }
    } catch {
      setBackendStatus('error')
    }
  }

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div className="home">
      {/* Header */}
      <header className="home-header">
        <div className="header-brand">
          <span className="brand-name">BurpKiller</span>
        </div>

        <nav className="header-nav">
          {user ? (
            <div className="user-section">
              <span className="user-name">{user.username}</span>
              <button className="btn btn-secondary" onClick={handleLogout}>
                Logout
              </button>
            </div>
          ) : (
            <div className="auth-section">
              <button className="btn btn-secondary" onClick={() => navigate('/login')}>
                Login
              </button>
              <button className="btn btn-primary" onClick={() => navigate('/register')}>
                Register
              </button>
            </div>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <h1 className="hero-title">Web Security Testing</h1>
        <p className="hero-subtitle">
          Outil collaboratif de reconnaissance et d'analyse de securite web.
        </p>
        <div className="hero-actions">
          {user ? (
            <button className="btn btn-primary btn-large" onClick={() => navigate('/investigations')}>
              Mes enquetes
            </button>
          ) : (
            <button className="btn btn-primary btn-large" onClick={() => navigate('/register')}>
              Commencer
            </button>
          )}
        </div>
      </section>

      {/* Footer avec status */}
      <footer className="home-footer">
        <div className="status-indicator">
          <span className={`status-dot status-${backendStatus}`}></span>
          <span className="status-text">
            {backendStatus === 'checking' && 'Connexion...'}
            {backendStatus === 'connected' && 'Backend connecte'}
            {backendStatus === 'error' && 'Backend hors ligne'}
          </span>
        </div>
      </footer>
    </div>
  )
}

export default Home

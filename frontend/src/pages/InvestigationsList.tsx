import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './InvestigationsList.css'

interface Investigation {
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

function InvestigationsList() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const API_URL = ''

  const [investigations, setInvestigations] = useState<Investigation[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Form state pour creation
  const [newName, setNewName] = useState('')
  const [newUrl, setNewUrl] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)
  const [isCollaborative, setIsCollaborative] = useState(false)

  // Charger les enquetes au montage
  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    loadInvestigations()
  }, [user])

  const loadInvestigations = async () => {
    try {
      const response = await fetch(`${API_URL}/api/investigations`, {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setInvestigations(data)
      }
    } catch (error) {
      console.error('Erreur chargement enquetes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const response = await fetch(`${API_URL}/api/investigations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name: newName,
          target_url: newUrl,
          description: newDescription,
          is_public: isPublic,
          is_collaborative: isCollaborative
        })
      })

      if (response.ok) {
        const newInvestigation = await response.json()
        setInvestigations([...investigations, newInvestigation])
        setShowCreateModal(false)
        resetForm()
      }
    } catch (error) {
      console.error('Erreur creation:', error)
    }
  }

  const resetForm = () => {
    setNewName('')
    setNewUrl('')
    setNewDescription('')
    setIsPublic(false)
    setIsCollaborative(false)
  }

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  if (loading) {
    return <div className="loading">Chargement...</div>
  }

  return (
    <div className="investigations-page">
      {/* Header */}
      <header className="page-header">
        <div className="header-brand" onClick={() => navigate('/')}>
          <span className="brand-name">BurpKiller</span>
        </div>
        <nav className="header-nav">
          <span className="user-name">{user?.username}</span>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </header>

      {/* Content */}
      <main className="page-content">
        <div className="content-header">
          <h1>Mes enquetes</h1>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            Nouvelle enquete
          </button>
        </div>

        {investigations.length === 0 ? (
          <div className="empty-state">
            <p>Aucune enquete pour le moment.</p>
            <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
              Creer ma premiere enquete
            </button>
          </div>
        ) : (
          <div className="investigations-list">
            {investigations.map(inv => (
              <div
                key={inv.id}
                className="investigation-card"
                onClick={() => navigate(`/investigation/${inv.id}`)}
              >
                <div className="card-header">
                  <h3 className="card-title">{inv.name}</h3>
                  <div className="card-badges">
                    {inv.is_public && <span className="badge badge-public">Public</span>}
                    {inv.is_collaborative && <span className="badge badge-collab">Collaboratif</span>}
                  </div>
                </div>
                <p className="card-url">{inv.target_url}</p>
                {inv.description && <p className="card-description">{inv.description}</p>}
                <div className="card-footer">
                  <span className="card-owner">Par {inv.owner.username}</span>
                  <span className="card-date">{new Date(inv.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Modal creation */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Nouvelle enquete</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Nom</label>
                <input
                  type="text"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  placeholder="Ex: Audit Site Client"
                  required
                />
              </div>
              <div className="form-group">
                <label>URL cible</label>
                <input
                  type="text"
                  value={newUrl}
                  onChange={e => setNewUrl(e.target.value)}
                  placeholder="https://example.com"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description (optionnel)</label>
                <textarea
                  value={newDescription}
                  onChange={e => setNewDescription(e.target.value)}
                  placeholder="Description de l'enquete..."
                  rows={3}
                />
              </div>
              <div className="form-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isCollaborative}
                    onChange={e => setIsCollaborative(e.target.checked)}
                  />
                  Collaborative
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isPublic}
                    onChange={e => setIsPublic(e.target.checked)}
                  />
                  Publique
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Annuler
                </button>
                <button type="submit" className="btn btn-primary">
                  Creer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default InvestigationsList

import { useEffect, useState } from 'react'
import './ActiveUsers.css'

interface ActiveUser {
  id: string
  username: string
  page: string
  last_seen: number
}

export default function ActiveUsers() {
  const [users, setUsers] = useState<ActiveUser[]>([])
  const [loading, setLoading] = useState(true)

  async function fetchUsers() {
    try {
      const res = await fetch('/api/presence/active', {
        credentials: 'include'
      })
      const json = await res.json()
      setUsers(json.users || [])
    } catch (e) {
      console.error('Erreur chargement utilisateurs:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
    const interval = setInterval(fetchUsers, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="active-users">
        <h5>Utilisateurs actifs</h5>
        <p className="loading-text">Chargement...</p>
      </div>
    )
  }

  return (
    <div className="active-users">
      <h5>Utilisateurs actifs ({users.length})</h5>
      <ul className="users-list">
        {users.map(u => (
          <li key={u.id} className="user-item">
            <span className="user-status-dot"></span>
            <span className="user-name">{u.username}</span>
            <span className="user-page">{u.page}</span>
            <span className="user-time">{u.last_seen}s</span>
          </li>
        ))}
        {users.length === 0 && (
          <li className="no-users">Aucun utilisateur actif</li>
        )}
      </ul>
    </div>
  )
}

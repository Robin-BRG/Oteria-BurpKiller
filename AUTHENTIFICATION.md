# Systeme d'Authentification Oteria

## Architecture

Le systeme d'authentification suit le modele **session-based** (similaire a Rails avec Devise) :

- **Backend** : Flask-Login gere les sessions avec cookies httpOnly
- **Frontend** : React avec AuthContext pour l'etat global de l'utilisateur
- **Base de donnees** : SQLite (dev) ou PostgreSQL (production)

---

## Structure Backend

### Fichiers crees

- `models.py` : Modele User (equivalent ActiveRecord)
- `auth.py` : Routes d'authentification (Blueprint)
- `init_db.py` : Script d'initialisation de la DB
- `.env` : Variables d'environnement

### Routes API

| Route | Methode | Description |
|-------|---------|-------------|
| `/api/register` | POST | Inscription (email, username, password) |
| `/api/login` | POST | Connexion (email, password) |
| `/api/logout` | POST | Deconnexion (requiert auth) |
| `/api/me` | GET | Utilisateur connecte (requiert auth) |
| `/api/check-auth` | GET | Verifier si connecte |

### Modele User

```python
class User:
    id: int
    email: str (unique)
    username: str (unique)
    password_hash: str (bcrypt)
    created_at: datetime
    updated_at: datetime
```

---

## Structure Frontend

### Fichiers crees

- `context/AuthContext.tsx` : Context React pour l'auth globale
- `pages/Login.tsx` : Page de connexion
- `pages/Register.tsx` : Page d'inscription
- `pages/Auth.css` : Styles minimalistes des formulaires

### AuthContext

Le context expose :

```typescript
{
  user: User | null,          // Utilisateur connecte
  loading: boolean,           // Chargement initial
  login(email, password),     // Fonction de connexion
  register(email, username, password), // Fonction d'inscription
  logout(),                   // Fonction de deconnexion
  checkAuth()                 // Verifier l'auth
}
```

### Utilisation

```tsx
import { useAuth } from '../context/AuthContext'

function MyComponent() {
  const { user, logout } = useAuth()
  
  if (user) {
    return <div>Hello, {user.username}!</div>
  }
  return <div>Not logged in</div>
}
```

---

## Securite

### Backend

- **Mots de passe** : Hashes avec bcrypt (salt automatique)
- **Sessions** : Cookies httpOnly + SameSite=Lax
- **Validation** : Email format, longueur min password (6), username (3)
- **CORS** : Restreint a `http://localhost:5173` avec credentials

### Frontend

- **Cookies** : Geres automatiquement par le navigateur
- **HTTPS** : Obligatoire en production
- **XSS** : React echappe automatiquement le contenu

---

## Installation

### 1. Installer les dependances backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip install flask-sqlalchemy flask-login flask-bcrypt psycopg2-binary python-dotenv
```

### 2. Initialiser la base de donnees

```bash
python init_db.py
```

### 3. Lancer le backend

```bash
python app.py
```

### 4. Le frontend n'a pas de nouvelle dependance

React Router et le context sont deja inclus.

---

## Migration vers PostgreSQL (Production)

1. Installer PostgreSQL sur le serveur

2. Creer la base de donnees :
```sql
CREATE DATABASE oteria_db;
CREATE USER oteria_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE oteria_db TO oteria_user;
```

3. Modifier `.env` :
```env
DATABASE_URL=postgresql://oteria_user:votre_mot_de_passe@localhost:5432/oteria_db
SECRET_KEY=generer-une-cle-aleatoire-longue-et-securisee
FLASK_ENV=production
FLASK_DEBUG=False
```

4. Re-initialiser :
```bash
python init_db.py
```

---

## Differences avec Rails

| Rails (Devise) | Flask (Manuel) |
|----------------|----------------|
| `rails generate devise User` | `models.py` manuel |
| `devise :database_authenticatable` | Flask-Login + bcrypt |
| `before_action :authenticate_user!` | `@login_required` decorator |
| Routes auto (`/users/sign_in`) | Routes manuelles (`/api/login`) |
| Sessions cookies auto | Configuration CORS manuelle |

**Avantage Flask** : Plus de controle, moins de magie
**Avantage Rails** : Setup en 5 minutes

---

## Tests

### Test de l'inscription

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'
```

### Test de la connexion

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' \
  -c cookies.txt
```

### Test de l'utilisateur connecte

```bash
curl http://localhost:5000/api/me -b cookies.txt
```

---

## Prochaines etapes possibles

- [ ] Protection des routes TestPage (requiert connexion)
- [ ] Scripts personnels par utilisateur
- [ ] Reset de mot de passe par email
- [ ] OAuth (Google, GitHub)
- [ ] Roles et permissions (admin, user)
- [ ] Historique d'execution des scripts

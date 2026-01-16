import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Home from './pages/Home'
import TestPage from './pages/TestPage'
import Login from './pages/Login'
import Register from './pages/Register'
import InvestigationsList from './pages/InvestigationsList'
import Investigation from './pages/Investigation'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/test" element={<TestPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/investigations" element={<InvestigationsList />} />
          <Route path="/investigation/:id" element={<Investigation />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App

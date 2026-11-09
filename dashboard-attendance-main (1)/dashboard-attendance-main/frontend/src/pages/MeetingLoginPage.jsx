import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setMeetingAuth } from '../meetingApi.js'

export default function MeetingLoginPage({ onAuthSuccess }) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleLogin = async () => {
    if (!email || !password) {
      setError('All fields are required')
      return
    }

    try {
      const response = await fetch('http://127.0.0.1:8001/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()
      if (!response.ok) {
        setError(data.detail || 'Login failed')
        return
      }

      setMeetingAuth(data.user, data.access_token)
      if (onAuthSuccess) onAuthSuccess()
      navigate('/meeting-history')
    } catch (err) {
      setError('Server error')
    }
  }

  return (
    <div className="meeting-shell">
      <div className="chart-card meeting-panel meeting-auth-panel">
        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Meeting Account</p>
            <h2>Login</h2>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="meeting-form-grid">
          <label className="form-field">
            <span>Email</span>
            <input className="form-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Corporate Email" />
          </label>

          <label className="form-field">
            <span>Password</span>
            <input className="form-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          </label>
        </div>

        <button className="primary-btn meeting-action-btn" onClick={handleLogin}>Login</button>

        <div className="meeting-auth-switch">
          New user? <Link to="/meeting-register">Register</Link>
        </div>
      </div>
    </div>
  )
}

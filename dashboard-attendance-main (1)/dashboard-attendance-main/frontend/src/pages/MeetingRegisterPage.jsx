import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { setMeetingAuth } from '../meetingApi.js'

export default function MeetingRegisterPage({ onAuthSuccess }) {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')

  const handleRegister = async () => {
    if (!name || !email || !password || !confirmPassword) {
      setError('All fields are required')
      return
    }

    if (name.trim().length < 3) {
      setError('Name must be at least 3 characters')
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setError('Enter valid email')
      return
    }

    if (!email.endsWith('@mph.com')) {
      setError('Use corporate email (@mph.com)')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/
    if (!passwordRegex.test(password)) {
      setError('Password must contain uppercase, lowercase and number')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    try {
      const response = await fetch('http://127.0.0.1:8001/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      })

      const data = await response.json()
      if (!response.ok) {
        setError(data.detail || 'Registration failed')
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
            <h2>Register</h2>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="meeting-form-grid">
          <label className="form-field">
            <span>Full Name</span>
            <input className="form-input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Full Name" />
          </label>

          <label className="form-field">
            <span>Corporate Email</span>
            <input className="form-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Corporate Email" />
          </label>

          <label className="form-field">
            <span>Password</span>
            <input className="form-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
          </label>

          <label className="form-field">
            <span>Confirm Password</span>
            <input className="form-input" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm Password" />
          </label>
        </div>

        <button className="primary-btn meeting-action-btn" onClick={handleRegister}>Register</button>

        <div className="meeting-auth-switch">
          Already have an account? <Link to="/meeting-login">Login</Link>
        </div>
      </div>
    </div>
  )
}

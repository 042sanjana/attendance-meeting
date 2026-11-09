import React from 'react'
import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Users, UploadCloud, BarChart3, Building2, ClipboardList, Mic, History, CheckSquare, CalendarRange, LogIn, UserPlus, LogOut, UserCircle2, GitBranch } from 'lucide-react'
import ResetDataButton from './ResetDataButton.jsx'

export default function Sidebar({ onUploadClick, onReset, meetingUser = {}, onMeetingLogout }) {
  const isLoggedIn = Boolean(meetingUser?.id || meetingUser?.email)

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon"><Building2 size={20} /></div>
        <div>
          <div className="brand-title">HR Portal</div>
          <div className="brand-subtitle">Attendance System</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/odc-tracker" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><ClipboardList size={18} /><span>ODC Tracker</span></NavLink>
        <NavLink to="/organization-hierarchy" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><GitBranch size={18} /><span>Hierarchy</span></NavLink>
        <a className="nav-item" href="#employees-section">
          <Users size={18} />
          <span>Employees</span>
        </a>
        <a className="nav-item" href="#charts-section">
          <BarChart3 size={18} />
          <span>Analytics</span>
        </a>

        <div className="sidebar-section-label">Meeting Management</div>
        <NavLink to="/meeting-upload" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Mic size={18} /><span>Upload Meeting</span></NavLink>
        <NavLink to="/meeting-history" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><History size={18} /><span>Meeting History</span></NavLink>
        <NavLink to="/meeting-tasks" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><CheckSquare size={18} /><span>Meeting Tasks</span></NavLink>
        <NavLink to="/meeting-calendar" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><CalendarRange size={18} /><span>Task Calendar</span></NavLink>

        <div className="sidebar-section-label">Meeting Account</div>
        {!isLoggedIn ? (
          <>
            <NavLink to="/meeting-login" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><LogIn size={18} /><span>Login</span></NavLink>
            <NavLink to="/meeting-register" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><UserPlus size={18} /><span>Register</span></NavLink>
          </>
        ) : (
          <>
            <div className="meeting-user-summary">
              <div className="meeting-user-avatar"><UserCircle2 size={18} /></div>
              <div className="meeting-user-meta">
                <strong>{meetingUser.name || 'Meeting User'}</strong>
                <span>{meetingUser.email || 'No email'}</span>
              </div>
            </div>
            <button type="button" className="nav-item" onClick={onMeetingLogout}>
              <LogOut size={18} />
              <span>Logout</span>
            </button>
          </>
        )}

        <button className="nav-item nav-upload" onClick={onUploadClick}>
          <UploadCloud size={18} />
          <span>Upload Excel</span>
        </button>
        <ResetDataButton onReset={onReset} className="nav-item nav-reset" />
      </nav>

      <div className="sidebar-footer">
        <div className="footer-card">
          <p>Need to add attendance?</p>
          <button onClick={onUploadClick}>Upload File</button>
        </div>
      </div>
    </aside>
  )
}
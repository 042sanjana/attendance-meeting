import React, { useState, useCallback, useEffect } from 'react'
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Topbar from './components/Topbar.jsx'
import Dashboard from './components/Dashboard.jsx'
import EmployeeDetail from './components/EmployeeDetail.jsx'
import UploadModal from './components/UploadModal.jsx'
import ODCTracker from './components/ODCTracker.jsx'
import MeetingUploadPage from './pages/MeetingUploadPage.jsx'
import MeetingHistoryPage from './pages/MeetingHistoryPage.jsx'
import MeetingTasksPage from './pages/MeetingTasksPage.jsx'
import MeetingCalendarPage from './pages/MeetingCalendarPage.jsx'
import MeetingDetailsPage from './pages/MeetingDetailsPage.jsx'
import MeetingLoginPage from './pages/MeetingLoginPage.jsx'
import MeetingRegisterPage from './pages/MeetingRegisterPage.jsx'
import { getCurrentMeetingUser, isMeetingAuthenticated, clearMeetingAuth } from './meetingApi.js'

function ProtectedMeetingRoute({ children }) {
  return isMeetingAuthenticated() ? children : <Navigate to="/meeting-login" replace />
}

export default function App() {
  const [uploadOpen, setUploadOpen] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [meetingUser, setMeetingUser] = useState(() => getCurrentMeetingUser())
  const navigate = useNavigate()

  useEffect(() => {
    const handleMeetingAuthChanged = () => setMeetingUser(getCurrentMeetingUser())
    window.addEventListener('meetingAuthChanged', handleMeetingAuthChanged)
    return () => window.removeEventListener('meetingAuthChanged', handleMeetingAuthChanged)
  }, [])

  const triggerRefresh = useCallback(() => setRefreshKey((k) => k + 1), [])

  const handleReset = useCallback(() => {
    triggerRefresh()
    navigate('/')
  }, [triggerRefresh, navigate])

  const handleMeetingLogout = useCallback(() => {
    clearMeetingAuth()
    setMeetingUser({})
    navigate('/meeting-login')
  }, [navigate])

  return (
    <div className="app-shell">
      <Sidebar
        onUploadClick={() => setUploadOpen(true)}
        onReset={handleReset}
        meetingUser={meetingUser}
        onMeetingLogout={handleMeetingLogout}
      />
      <div className="main-area">
        <Topbar onUploadClick={() => setUploadOpen(true)} />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard refreshKey={refreshKey} />} />
            <Route path="/employees/:empId" element={<EmployeeDetail />} />
            <Route path="/odc-tracker" element={<ODCTracker />} />

            <Route path="/meeting-login" element={<MeetingLoginPage onAuthSuccess={() => setMeetingUser(getCurrentMeetingUser())} />} />
            <Route path="/meeting-register" element={<MeetingRegisterPage onAuthSuccess={() => setMeetingUser(getCurrentMeetingUser())} />} />

            <Route path="/meeting-upload" element={<ProtectedMeetingRoute><MeetingUploadPage /></ProtectedMeetingRoute>} />
            <Route path="/meeting-history" element={<ProtectedMeetingRoute><MeetingHistoryPage /></ProtectedMeetingRoute>} />
            <Route path="/meeting-tasks" element={<ProtectedMeetingRoute><MeetingTasksPage /></ProtectedMeetingRoute>} />
            <Route path="/meeting-calendar" element={<ProtectedMeetingRoute><MeetingCalendarPage /></ProtectedMeetingRoute>} />
            <Route path="/meeting/:id" element={<ProtectedMeetingRoute><MeetingDetailsPage /></ProtectedMeetingRoute>} />
          </Routes>
        </div>
      </div>
      {uploadOpen && (
        <UploadModal
          onClose={() => setUploadOpen(false)}
          onSuccess={() => {
            triggerRefresh()
          }}
        />
      )}
    </div>
  )
}
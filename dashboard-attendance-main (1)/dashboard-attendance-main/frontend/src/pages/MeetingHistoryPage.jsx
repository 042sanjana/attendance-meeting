import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FaTrash, FaEdit, FaSave, FaTimes, FaEnvelope } from 'react-icons/fa'
import { MEETING_API_BASE, getCurrentMeetingUser } from '../meetingApi'
import axios from 'axios'

export default function MeetingHistoryPage() {
  const navigate = useNavigate()
  const [meetings, setMeetings] = useState([])
  const [allMeetings, setAllMeetings] = useState([])
  const [selectedDate, setSelectedDate] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editedSummary, setEditedSummary] = useState('')
  const [showMailModal, setShowMailModal] = useState(false)
  const [mailTo, setMailTo] = useState('')
  const [mailSubject, setMailSubject] = useState('')
  const [selectedMeeting, setSelectedMeeting] = useState(null)

  const loadMeetings = async () => {
    const user = getCurrentMeetingUser()
    const userId = user?.id

    if (!userId) {
      alert('Meeting notes user is not available. Please log in via the Meeting Notes auth flow first.')
      return
    }

    try {
      const response = await axios.get(`${MEETING_API_BASE}/meetings/user/${userId}`)
      setMeetings(response.data)
      setAllMeetings(response.data)
    } catch (error) {
      console.error(error)
      alert('Failed to load meetings.')
    }
  }

  useEffect(() => {
    loadMeetings()
  }, [])

  const deleteMeeting = async (meetingId) => {
    const confirmed = window.confirm('Delete this meeting record?')
    if (!confirmed) return

    try {
      await axios.delete(`${MEETING_API_BASE}/meetings/${meetingId}`)
      const updated = meetings.filter((meeting) => meeting.id !== meetingId)
      setMeetings(updated)
      setAllMeetings(updated)
      alert('Meeting deleted successfully.')
    } catch (error) {
      console.error(error)
      alert('Failed to delete meeting.')
    }
  }

  const saveSummary = async (meetingId) => {
    try {
      await axios.put(`${MEETING_API_BASE}/meetings/${meetingId}/summary`, { summary: editedSummary })
      const updated = meetings.map((meeting) =>
        meeting.id === meetingId ? { ...meeting, summary: editedSummary } : meeting,
      )
      setMeetings(updated)
      setAllMeetings(updated)
      setEditingId(null)
      alert('Summary updated successfully.')
    } catch (error) {
      console.error(error)
      alert('Failed to update summary.')
    }
  }

  const openMailPopup = (meeting) => {
    setSelectedMeeting(meeting)
    setMailTo('')
    setMailSubject(`Meeting Summary - ${meeting.file_name}`)
    setShowMailModal(true)
  }

  const sendMail = () => {
    if (!mailTo.trim() || !selectedMeeting) {
      alert('Please enter a recipient email.')
      return
    }

    const body = `Hello,\n\nPlease find the meeting summary below.\n\n---------------------------------------\n\n${selectedMeeting.summary}\n\nRegards,\nAI Meeting Notes System`
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(mailTo)}&su=${encodeURIComponent(mailSubject)}&body=${encodeURIComponent(body)}`
    window.open(gmailUrl, '_blank')
    setShowMailModal(false)
  }

  const filteredByDate = () => {
    if (!selectedDate) {
      alert('Please select a date first.')
      return
    }

    const filtered = allMeetings.filter((meeting) => {
      const createdDate = new Date(meeting.created_at).toISOString().split('T')[0]
      return createdDate === selectedDate
    })
    setMeetings(filtered)
  }

  return (
    <div className="meeting-shell">
      <div className="chart-card meeting-panel">
        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Meeting Management</p>
            <h2>Meeting History</h2>
          </div>
        </div>

        <div className="meeting-toolbar">
          <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
          <button className="secondary-btn" onClick={filteredByDate}>Search</button>
          <button className="secondary-btn" onClick={() => { setMeetings(allMeetings); setSelectedDate('') }}>Show all</button>
        </div>

        <div className="meeting-grid">
          {meetings.length === 0 ? (
            <div className="empty-state">No meetings found.</div>
          ) : (
            meetings.map((meeting) => (
              <div
                key={meeting.id}
                className="meeting-card"
                onClick={() => {
                  if (editingId !== meeting.id) navigate(`/meeting/${meeting.id}`)
                }}
              >
                <button
                  className="delete-btn"
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteMeeting(meeting.id)
                  }}
                >
                  <FaTrash />
                </button>

                <h3>🎤 {meeting.file_name}</h3>

                {editingId === meeting.id ? (
                  <>
                    <textarea
                      className="meeting-summary-editor"
                      value={editedSummary}
                      onChange={(e) => setEditedSummary(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="meeting-inline-actions">
                      <FaSave className="meeting-icon" title="Save" onClick={(e) => { e.stopPropagation(); saveSummary(meeting.id) }} />
                      <FaTimes className="meeting-icon" title="Cancel" onClick={(e) => { e.stopPropagation(); setEditingId(null); setEditedSummary('') }} />
                    </div>
                  </>
                ) : (
                  <div className="meeting-summary-block">
                    <div className="meeting-summary-text">{meeting.summary}</div>
                    <div className="meeting-inline-actions">
                      <FaEdit className="meeting-icon" title="Edit summary" onClick={(e) => { e.stopPropagation(); setEditingId(meeting.id); setEditedSummary(meeting.summary) }} />
                      <FaEnvelope className="meeting-icon" title="Send summary" onClick={(e) => { e.stopPropagation(); openMailPopup(meeting) }} />
                    </div>
                  </div>
                )}

                <div className="meeting-card-date">{new Date(meeting.created_at).toLocaleString()}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {showMailModal && (
        <div className="mail-modal-overlay" onClick={() => setShowMailModal(false)}>
          <div className="mail-modal" onClick={(e) => e.stopPropagation()}>
            <h3>📧 Send Meeting Summary</h3>
            <label>Recipient Email</label>
            <input type="email" value={mailTo} onChange={(e) => setMailTo(e.target.value)} />
            <label>Subject</label>
            <input type="text" value={mailSubject} onChange={(e) => setMailSubject(e.target.value)} />
            <label>Summary Preview</label>
            <textarea readOnly rows={10} value={selectedMeeting?.summary || ''} />
            <div className="mail-buttons">
              <button className="secondary-btn" onClick={() => setShowMailModal(false)}>Cancel</button>
              <button className="primary-btn" onClick={sendMail}>Open Gmail</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

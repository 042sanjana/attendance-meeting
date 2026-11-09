import { useState } from 'react'
import axios from 'axios'
import { MEETING_API_BASE, getMeetingAuthHeaders } from '../meetingApi'

export default function MeetingUploadPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleSubmit = async () => {
    if (!file) {
      alert('Please select an audio file.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      const response = await axios.post(`${MEETING_API_BASE}/meetings/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getMeetingAuthHeaders(),
        },
      })
      setResult(response.data)
    } catch (error) {
      console.error(error)
      alert(error.response?.data?.detail || 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="meeting-shell">
      <div className="chart-card meeting-panel">
        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Meeting Management</p>
            <h2>Upload Meeting</h2>
          </div>
        </div>

        <div className="meeting-upload-box">
          <input type="file" accept=".wav,.mp3,.m4a" onChange={(e) => setFile(e.target.files[0])} />
        </div>

        {file && <div className="meeting-selected-file">📁 {file.name}</div>}

        <button className="primary-btn meeting-action-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Analyzing meeting...' : 'Generate notes'}
        </button>

        {loading && (
          <div className="meeting-loading">
            <div className="meeting-spinner" />
            <p>Whisper → BART → Task Extraction</p>
          </div>
        )}

        {result && (
          <div className="meeting-result-grid">
            <div className="summary-card accent-blue">
              <div className="summary-card-icon">
                <span>📂</span>
              </div>
              <div className="summary-card-body">
                <div className="summary-card-value">{result.tasks?.length || 0}</div>
                <div className="summary-card-label">Tasks detected</div>
              </div>
            </div>

            <div className="chart-card meeting-result-card">
              <h3>Meeting summary</h3>
              <p>{result.summary}</p>
            </div>

            <div className="chart-card meeting-result-card">
              <h3>Action items</h3>
              {result.tasks?.length ? (
                result.tasks.map((task, index) => (
                  <div key={index} className="meeting-task-item">
                    <strong>{task.task}</strong>
                    <div>Owner: {task.owner}</div>
                    <div>Deadline: {task.deadline_text || task.deadline_date || 'Not specified'}</div>
                    <div>Priority: {task.priority}</div>
                    <div>Status: {task.status}</div>
                  </div>
                ))
              ) : (
                <p>No tasks detected.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { MEETING_API_BASE } from '../meetingApi'

export default function MeetingDetailsPage() {
  const { id } = useParams()
  const [meeting, setMeeting] = useState(null)

  useEffect(() => {
    const fetchMeeting = async () => {
      try {
        const response = await axios.get(`${MEETING_API_BASE}/meetings/${id}`)
        setMeeting(response.data)
      } catch (error) {
        console.error(error)
      }
    }

    fetchMeeting()
  }, [id])

  if (!meeting) return <div className="meeting-shell"><div className="chart-card meeting-panel">Loading meeting...</div></div>

  return (
    <div className="meeting-shell">
      <div className="chart-card meeting-panel">
        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Meeting Management</p>
            <h2>{meeting.file_name}</h2>
          </div>
        </div>

        <div className="meeting-detail-block">
          <h3>Transcript</h3>
          <p>{meeting.transcript}</p>
        </div>

        <div className="meeting-detail-block">
          <h3>Summary</h3>
          <p>{meeting.summary}</p>
        </div>
      </div>
    </div>
  )
}

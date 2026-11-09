import { useEffect, useState } from 'react'
import Calendar from 'react-calendar'
import 'react-calendar/dist/Calendar.css'
import axios from 'axios'
import { MEETING_API_BASE, getCurrentMeetingUser } from '../meetingApi'

export default function MeetingCalendarPage() {
  const [tasks, setTasks] = useState([])
  const [selectedDate, setSelectedDate] = useState(new Date())

  const formatDate = (date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const loadTasks = async () => {
    const user = getCurrentMeetingUser()
    const userId = user?.id

    if (!userId) {
      alert('Meeting notes user is not available. Please log in via the Meeting Notes auth flow first.')
      return
    }

    try {
      const response = await axios.get(`${MEETING_API_BASE}/meetings/user/${userId}/tasks`)
      setTasks(response.data)
    } catch (error) {
      console.error(error)
      alert('Failed to load task calendar.')
    }
  }

  useEffect(() => {
    loadTasks()
  }, [])

  const updateStatus = async (taskId, status) => {
    try {
      await axios.put(`${MEETING_API_BASE}/meetings/tasks/${taskId}/status`, null, { params: { status } })
      setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, status } : task)))
    } catch (error) {
      console.error(error)
      alert('Failed to update task status.')
    }
  }

  const updateDeadline = async (taskId, deadlineDate) => {
    try {
      await axios.put(`${MEETING_API_BASE}/meetings/tasks/${taskId}/deadline`, null, { params: { deadline_date: deadlineDate } })
      setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, deadline_date: deadlineDate } : task)))
      alert('Deadline updated.')
    } catch (error) {
      console.error(error)
      alert('Failed to update deadline.')
    }
  }

  const exportCalendar = () => {
    const user = getCurrentMeetingUser()
    if (!user?.id) return
    window.open(`${MEETING_API_BASE}/meetings/tasks/export/${user.id}`, '_blank')
  }

  const tileContent = ({ date, view }) => {
    if (view !== 'month') return null
    const currentDate = formatDate(date)
    const count = tasks.filter((task) => task.deadline_date?.substring(0, 10) === currentDate).length
    return count ? <div className="meeting-calendar-badge">{count}</div> : null
  }

  const selectedDateString = formatDate(selectedDate)
  const tasksForDate = tasks.filter((task) => task.deadline_date?.substring(0, 10) === selectedDateString)

  return (
    <div className="meeting-shell">
      <div className="chart-card meeting-panel">
        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Meeting Management</p>
            <h2>Task Calendar</h2>
          </div>
        </div>

        <Calendar onChange={setSelectedDate} value={selectedDate} tileContent={tileContent} />

        <div className="meeting-calendar-section">
          <h3>Tasks for {selectedDateString}</h3>

          {tasksForDate.length === 0 ? (
            <div className="empty-state">No tasks on this date.</div>
          ) : (
            tasksForDate.map((task) => (
              <div key={task.id} className="meeting-calendar-task">
                <h4>{task.task}</h4>
                <p><strong>Owner:</strong> {task.owner}</p>
                <p><strong>Priority:</strong> {task.priority}</p>

                <div className="meeting-deadline-box">
                  <label>Deadline</label>
                  <input type="date" value={task.deadline_date || ''} onChange={(e) => updateDeadline(task.id, e.target.value)} />
                </div>

                <div className="meeting-status-box">
                  <label>Status</label>
                  <select value={task.status || 'Pending'} onChange={(e) => updateStatus(task.id, e.target.value)}>
                    <option value="Pending">Pending</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>
              </div>
            ))
          )}

          <button className="primary-btn meeting-action-btn" onClick={exportCalendar}>Export To Calendar</button>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import axios from 'axios'
import { MEETING_API_BASE, getCurrentMeetingUser } from '../meetingApi'

export default function MeetingTasksPage() {
  const [tasks, setTasks] = useState([])

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
      alert('Failed to load tasks.')
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

  return (
    <div className="meeting-shell">
      <div className="chart-card meeting-panel">
        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Meeting Management</p>
            <h2>Meeting Tasks</h2>
          </div>
        </div>

        <div className="meeting-task-table-wrap">
          <table className="meeting-task-table">
            <thead>
              <tr>
                <th>Owner</th>
                <th>Task</th>
                <th>Deadline</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan="4">No tasks found.</td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr key={task.id}>
                    <td>{task.owner}</td>
                    <td>{task.task}</td>
                    <td>{task.deadline_date || '—'}</td>
                    <td>
                      <select
                        value={task.status || 'Pending'}
                        onChange={(e) => updateStatus(task.id, e.target.value)}
                        className="meeting-status-select"
                      >
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

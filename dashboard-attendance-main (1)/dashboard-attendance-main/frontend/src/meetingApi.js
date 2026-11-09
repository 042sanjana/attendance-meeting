export const MEETING_API_BASE = 'http://127.0.0.1:8001'

export const getCurrentMeetingUser = () => {
  try {
    const stored = localStorage.getItem('meeting_user')
    return stored ? JSON.parse(stored) : {}
  } catch (error) {
    return {}
  }
}

export const getMeetingToken = () => localStorage.getItem('meeting_token') || ''

export const isMeetingAuthenticated = () => Boolean(getMeetingToken())

export const getMeetingAuthHeaders = () => {
  const token = getMeetingToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const setMeetingAuth = (user, token) => {
  localStorage.setItem('meeting_user', JSON.stringify(user))
  localStorage.setItem('meeting_token', token)
  window.dispatchEvent(new Event('meetingAuthChanged'))
}

export const clearMeetingAuth = () => {
  localStorage.removeItem('meeting_user')
  localStorage.removeItem('meeting_token')
  window.dispatchEvent(new Event('meetingAuthChanged'))
}

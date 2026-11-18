import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { Bot, Send, Sparkles, X, Mic, Square } from 'lucide-react'
import { getCurrentMeetingUser, getMeetingToken } from '../meetingApi'

const starters = [
  'Show the latest attendance summary',
  'Who is absent today?',
  'Show pending meeting tasks',
  'Give me an ODC summary',
]

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId] = useState(() => `workforce-${Date.now()}`)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'I can answer questions across attendance, hierarchy, meeting notes and ODC tracker.' },
  ])
  const [isRecording, setIsRecording] = useState(false)
  const scrollRef = useRef(null)
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])

  useEffect(() => {
    if (open && scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages, open, loading])

  const sendMessage = async (question) => {
    const text = (typeof question === 'string' ? question : message).trim()
    if (!text || loading) return

    setMessage('')
    setMessages((current) => [...current, { role: 'user', content: text }])
    setLoading(true)

    try {
      const meetingUser = getCurrentMeetingUser()
      const token = getMeetingToken()
      const response = await axios.post('/api/chatbot/chat', {
        message: text,
        session_id: conversationId,
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      setMessages((current) => [...current, {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        reportingPeriod: response.data.reporting_period,
        chart: response.data.chart,
      }])
    } catch (error) {
      const detail = error?.response?.data?.detail
      setMessages((current) => [...current, {
        role: 'assistant',
        content: typeof detail === 'string' ? detail : 'I could not retrieve the workspace data. Please try again.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const renderChart = (chart) => {
    if (!chart?.labels?.length) return null
    const rawValues = chart.series?.[0]?.values || []
    const values = rawValues.map((value) => typeof value === 'number' ? value : 0)
    const maximum = Math.max(...values, 1)

    return (
      <div className="chatbot-chart">
        {chart.title && <strong>{chart.title}</strong>}
        {chart.labels.map((label, index) => (
          <div className="chatbot-chart-row" key={`${label}-${index}`}>
            <span>{label}</span>
            <div><i style={{ width: `${Math.max(6, ((values[index] || 0) / maximum) * 100)}%` }} /></div>
            <b>{rawValues[index] ?? 0}</b>
          </div>
        ))}
      </div>
    )
  }

  const stopRecording = () => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop()
    }
  }

  const startRecording = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
        throw new Error('Audio recording is not supported in this browser.')
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
      streamRef.current = stream
      chunksRef.current = []

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      const recorder = new MediaRecorder(stream, { mimeType })
      recorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data?.size) chunksRef.current.push(event.data)
      }

      recorder.onstop = async () => {
        streamRef.current?.getTracks().forEach((track) => track.stop())
        streamRef.current = null
        setIsRecording(false)

        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        if (!blob.size) {
          setMessages((current) => [...current, { role: 'assistant', content: 'No audio was captured. Please record again.' }])
          return
        }

        const formData = new FormData()
        formData.append('file', blob, `live-meeting-${Date.now()}.webm`)
        setLoading(true)

        try {
          const response = await axios.post('/api/chatbot/audio/process', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })
          const data = response.data
          const transcript = data.transcript || ''
          const summary = data.summary
          const decisions = data.decisions || []
          const tasks = data.tasks || []

          const sections = [`Live meeting transcript processed.`,]
          if (summary) sections.push(`Summary: ${summary}`)
          if (decisions.length) sections.push(`Decisions: ${decisions.join('; ')}`)
          if (tasks.length) sections.push(`Tasks: ${tasks.map((task) => `${task.owner || 'Unknown'} — ${task.task || 'Unspecified'}`).join('; ')}`)
          if (transcript) sections.push(`Transcript: ${transcript.slice(0, 1600)}${transcript.length > 1600 ? '...' : ''}`)

          setMessages((current) => [...current, {
            role: 'assistant',
            content: sections.join('\n\n'),
            sources: ['Whisper transcription', 'Meeting processor'],
          }])
        } catch (error) {
          const detail = error?.response?.data?.detail
          setMessages((current) => [...current, {
            role: 'assistant',
            content: typeof detail === 'string' ? detail : 'The live recording could not be processed.',
          }])
        } finally {
          setLoading(false)
        }
      }

      recorder.start(1000)
      setIsRecording(true)
    } catch (error) {
      setMessages((current) => [...current, {
        role: 'assistant',
        content: 'Microphone access is unavailable. Please allow microphone permission and try again.',
      }])
    }
  }

  return (
    <>
      {open && (
        <aside className="chatbot-panel" aria-label="Workforce AI Assistant">
          <div className="chatbot-header">
            <div className="chatbot-title">
              <div className="chatbot-title-icon"><Sparkles size={17} /></div>
              <div><strong>Workforce Assistant</strong><span>Attendance · Hierarchy · Meetings · ODC</span></div>
            </div>
            <button type="button" className="chatbot-close" onClick={() => setOpen(false)} aria-label="Close assistant"><X size={18} /></button>
          </div>

          <div className="chatbot-messages" ref={scrollRef}>
            {messages.map((item, index) => (
              <div key={`${item.role}-${index}`} className={`chatbot-message ${item.role}`}>
                <div className="chatbot-bubble">
                  {item.content}
                  {renderChart(item.chart)}
                  {item.reportingPeriod && <div className="chatbot-meta">Reporting period: {item.reportingPeriod}</div>}
                  {item.sources?.length > 0 && <div className="chatbot-meta">Sources: {item.sources.join(', ')}</div>}
                </div>
              </div>
            ))}

            {loading && <div className="chatbot-message assistant"><div className="chatbot-bubble chatbot-thinking"><span /><span /><span /></div></div>}

            {messages.length === 1 && (
              <div className="chatbot-starters">
                {starters.map((question) => (
                  <button type="button" key={question} onClick={() => sendMessage(question)}>{question}</button>
                ))}
              </div>
            )}
          </div>

          <form className="chatbot-form" onSubmit={(event) => { event.preventDefault(); sendMessage() }}>
            <input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask across the workforce system..." aria-label="Chat message" />
            <button
              type="button"
              className={isRecording ? 'chatbot-mic recording' : 'chatbot-mic'}
              onClick={() => isRecording ? stopRecording() : startRecording()}
              aria-label={isRecording ? 'Stop recording' : 'Start live meeting recording'}
              disabled={loading}
            >
              {isRecording ? <Square size={17} /> : <Mic size={17} />}
            </button>
            <button type="submit" disabled={!message.trim() || loading} aria-label="Send message"><Send size={17} /></button>
          </form>
        </aside>
      )}

      <button type="button" className={`chatbot-fab ${open ? 'active' : ''}`} onClick={() => setOpen((current) => !current)} aria-label="Open Workforce Assistant">
        {open ? <X size={22} /> : <Bot size={23} />}
      </button>
    </>
  )
}

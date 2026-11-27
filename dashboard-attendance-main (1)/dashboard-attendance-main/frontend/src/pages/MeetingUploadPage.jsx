import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { MEETING_API_BASE, getMeetingAuthHeaders } from '../meetingApi'

const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return [hours, minutes, secs].map((value) => String(value).padStart(2, '0')).join(':')
}

export default function MeetingUploadPage() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const [recordingState, setRecordingState] = useState('idle')
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [recordingError, setRecordingError] = useState('')
  const [recordingBlob, setRecordingBlob] = useState(null)
  const [recordingUrl, setRecordingUrl] = useState('')

  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const submissionLockRef = useRef(false)
  const discardRef = useRef(false)

  const stopTracks = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }

  const clearTimer = () => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  useEffect(() => () => {
    clearTimer()
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    stopTracks()
    if (recordingUrl) URL.revokeObjectURL(recordingUrl)
  }, [])

  useEffect(() => {
    if (!recordingUrl) return
    return () => URL.revokeObjectURL(recordingUrl)
  }, [recordingUrl])

  const startTimer = () => {
    clearTimer()
    timerRef.current = window.setInterval(() => {
      setRecordingSeconds((value) => value + 1)
    }, 1000)
  }

  const getRecordingMimeType = () => {
    if (window.MediaRecorder?.isTypeSupported?.('audio/webm;codecs=opus')) return 'audio/webm;codecs=opus'
    if (window.MediaRecorder?.isTypeSupported?.('audio/webm')) return 'audio/webm'
    if (window.MediaRecorder?.isTypeSupported?.('audio/mp4')) return 'audio/mp4'
    return ''
  }

  const startRecording = async () => {
    if (recordingState === 'recording' || recordingState === 'paused') return
    discardRef.current = false
    setRecordingError('')

    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setRecordingError('Live recording is not supported in this browser.')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
      streamRef.current = stream
      chunksRef.current = []

      const mimeType = getRecordingMimeType()
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)

      recorder.ondataavailable = (event) => {
        if (event.data?.size) chunksRef.current.push(event.data)
      }

      recorder.onstop = () => {
        clearTimer()
        if (discardRef.current) {
          discardRef.current = false
          stopTracks()
          return
        }
        const actualMime = recorder.mimeType || mimeType || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: actualMime })
        if (!blob.size) {
          setRecordingError('No audio was captured. Please record again.')
          setRecordingBlob(null)
          setRecordingUrl('')
          setRecordingState('idle')
          stopTracks()
          return
        }
        const url = URL.createObjectURL(blob)
        setRecordingUrl((current) => {
          if (current) URL.revokeObjectURL(current)
          return url
        })
        setRecordingBlob(blob)
        setRecordingState('stopped')
        stopTracks()
      }

      recorder.onerror = () => {
        setRecordingError('The browser recording failed. Please try again.')
        setRecordingState('idle')
        clearTimer()
        stopTracks()
      }

      mediaRecorderRef.current = recorder
      recorder.start(1000)
      setRecordingSeconds(0)
      setRecordingState('recording')
      startTimer()
    } catch (error) {
      if (error?.name === 'NotAllowedError' || error?.name === 'PermissionDeniedError') {
        setRecordingError('Microphone permission was denied. Allow microphone access and try again.')
      } else if (error?.name === 'NotFoundError' || error?.name === 'DevicesNotFoundError') {
        setRecordingError('No microphone device was found.')
      } else {
        setRecordingError(error?.message || 'Microphone access is unavailable.')
      }
      setRecordingState('idle')
    }
  }

  const pauseRecording = () => {
    const recorder = mediaRecorderRef.current
    if (recorder?.state === 'recording') {
      recorder.pause()
      clearTimer()
      setRecordingState('paused')
    }
  }

  const resumeRecording = () => {
    const recorder = mediaRecorderRef.current
    if (recorder?.state === 'paused') {
      recorder.resume()
      setRecordingState('recording')
      startTimer()
    }
  }

  const stopRecording = () => {
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state !== 'inactive') recorder.stop()
  }

  const discardRecording = () => {
    discardRef.current = true
    const recorder = mediaRecorderRef.current
    if (recorder && recorder.state !== 'inactive') recorder.stop()
    if (recordingUrl) URL.revokeObjectURL(recordingUrl)
    setRecordingUrl('')
    setRecordingBlob(null)
    chunksRef.current = []
    setRecordingSeconds(0)
    setRecordingState('idle')
    setRecordingError('')
    clearTimer()
    stopTracks()
  }

  const handleSubmit = async () => {
    if (!file) {
      alert('Please select an audio file.')
      return
    }

    await processAudio(file)
  }

  const processAudio = async (audioFile) => {
    if (submissionLockRef.current) return
    submissionLockRef.current = true

    const formData = new FormData()
    formData.append('file', audioFile)

    try {
      setLoading(true)
      setRecordingError('')
      const response = await axios.post(`${MEETING_API_BASE}/meetings/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getMeetingAuthHeaders(),
        },
      })
      setResult(response.data)
    } catch (error) {
      console.error(error)
      setRecordingError(error.response?.data?.detail || 'Meeting processing failed.')
    } finally {
      setLoading(false)
      submissionLockRef.current = false
    }
  }

  const processLiveRecording = async () => {
    if (!recordingBlob) {
      setRecordingError('Stop the recording first, then generate meeting notes.')
      return
    }

    const mimeType = recordingBlob.type || 'audio/webm'
    const extension = mimeType.includes('mp4') ? 'm4a' : 'webm'
    const liveFile = new File([recordingBlob], `live-meeting-${Date.now()}.${extension}`, { type: mimeType })
    await processAudio(liveFile)
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
          <input type="file" accept=".wav,.mp3,.m4a" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </div>

        {file && <div className="meeting-selected-file">📁 {file.name}</div>}

        <button className="primary-btn meeting-action-btn" onClick={handleSubmit} disabled={loading || !file}>
          {loading ? 'Analyzing meeting...' : 'Generate notes'}
        </button>

        <hr />

        <div className="meeting-page-header">
          <div>
            <p className="eyebrow">Live Meeting</p>
            <h2>Record Live Meeting</h2>
          </div>
        </div>

        <div className="meeting-selected-file">
          Status: <strong>{recordingState === 'idle' ? 'Ready' : recordingState === 'paused' ? 'Paused' : recordingState === 'stopped' ? 'Stopped' : 'Recording'}</strong>
          {'  |  '}Duration: <strong>{formatDuration(recordingSeconds)}</strong>
        </div>

        {recordingError && <div className="meeting-selected-file">⚠️ {recordingError}</div>}

        <div className="meeting-inline-actions">
          <button type="button" className="secondary-btn" onClick={startRecording} disabled={loading || recordingState === 'recording' || recordingState === 'paused'}>
            Start Recording
          </button>
          <button type="button" className="secondary-btn" onClick={pauseRecording} disabled={recordingState !== 'recording'}>
            Pause
          </button>
          <button type="button" className="secondary-btn" onClick={resumeRecording} disabled={recordingState !== 'paused'}>
            Resume
          </button>
          <button type="button" className="primary-btn" onClick={stopRecording} disabled={recordingState !== 'recording' && recordingState !== 'paused'}>
            Stop Recording
          </button>
        </div>

        {recordingUrl && (
          <div className="meeting-detail-block">
            <h3>Recorded audio preview</h3>
            <audio controls src={recordingUrl} />
            <div className="meeting-inline-actions">
              <button type="button" className="secondary-btn" onClick={discardRecording} disabled={loading}>Discard Recording</button>
              <button type="button" className="primary-btn" onClick={processLiveRecording} disabled={loading}>Generate Meeting Notes</button>
            </div>
          </div>
        )}

        {loading && (
          <div className="meeting-loading">
            <div className="meeting-spinner" />
            <p>Whisper → Meeting extraction → Task extraction</p>
          </div>
        )}

        {result && (
          <div className="meeting-result-grid">
            <div className="summary-card accent-blue">
              <div className="summary-card-icon"><span>📂</span></div>
              <div className="summary-card-body">
                <div className="summary-card-value">{result.tasks?.length || 0}</div>
                <div className="summary-card-label">Tasks detected</div>
              </div>
            </div>

            {result.language && (
              <div className="chart-card meeting-result-card">
                <h3>Recording details</h3>
                <p>Language: {result.language}</p>
                <p>Duration: {formatDuration(Math.round(result.duration || 0))}</p>
              </div>
            )}

            <div className="chart-card meeting-result-card">
              <h3>Meeting summary</h3>
              <p>{result.summary}</p>
            </div>

            {result.decisions?.length > 0 && (
              <div className="chart-card meeting-result-card">
                <h3>Decisions</h3>
                {result.decisions.map((decision, index) => <p key={index}>{decision}</p>)}
              </div>
            )}

            {result.transcript && (
              <div className="chart-card meeting-result-card">
                <h3>Full transcript</h3>
                <p>{result.transcript}</p>
              </div>
            )}

            <div className="chart-card meeting-result-card">
              <h3>Action items</h3>
              {result.tasks?.length ? (
                result.tasks.map((task, index) => (
                  <div key={`${task.owner}-${task.task}-${index}`} className="meeting-task-item">
                    <strong>{task.task}</strong>
                    <div>Owner: {task.owner || 'Unknown'}</div>
                    <div>Employee ID: {task.employee_id || 'Not specified'}</div>
                    <div>Deadline: {task.deadline_text || task.deadline_date || 'Not specified'}</div>
                    <div>Priority: {task.priority || 'Not specified'}</div>
                    <div>Status: {task.status || 'Pending'}</div>
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

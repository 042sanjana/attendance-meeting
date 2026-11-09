import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./UploadMeeting.css";

function UploadMeeting() {

const [file, setFile] = useState(null);
const [loading, setLoading] = useState(false);
const [result, setResult] = useState(null);

const navigate = useNavigate();

const handleFileChange = (e) => {
setFile(e.target.files[0]);
};
const uploadAudio = async () => {

  if (!file) {
    alert("Please select an audio file");
    return;
  }

  try {

    setLoading(true);

  

  

    const formData = new FormData();

    formData.append(
      "file",
      file
    );
    const token=localStorage.getItem("token");
    const response =
      await axios.post(
        `http://127.0.0.1:8000/meetings/upload`,
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
              "Authorization":`Bearer ${token}`
          }
        }
      );

    console.log(
      response.data
    );

    setResult(
      response.data
    );

  } catch (error) {

    console.log(
      error.response?.data
    );

    alert(
      "Upload failed"
    );

  } finally {

    setLoading(false);

  }

};


return (

<div className="meeting-container">

  <div className="glass-card">

    <h1>
      🎙 AI Meeting Notes Generator
    </h1>

    <p>
      Upload a WAV, MP3 or M4A meeting recording and
      generate AI-powered meeting notes.
    </p>

    <div className="upload-box">

      <input
        type="file"
        accept=".wav,.mp3,.m4a"
        onChange={handleFileChange}
      />

    </div>

    {file && (

      <div className="selected-file">
        📁 {file.name}
      </div>

    )}

    <button
      onClick={uploadAudio}
      disabled={loading}
    >
      {
        loading
          ? "Analyzing Meeting..."
          : "Generate Notes"
      }
    </button>

    {loading && (

      <div className="loader-section">

        <div className="loader"></div>

        <p>
          Whisper → BART → Regex →
          Dateparser Processing...
        </p>

      </div>

    )}

    {result && (

      <div className="results">

        <div className="summary-card">

          <h2>
            📂 File Information
          </h2>

          <p>
            <strong>Meeting ID:</strong>
            {" "}
            {result.meeting_id}
          </p>

          <p>
            <strong>File Name:</strong>
            {" "}
            {result.file_name}
          </p>

          <p>
            <strong>Status:</strong>
            {" "}
            {
              result.success
                ? "Success ✅"
                : "Failed ❌"
            }
          </p>

          <p>
            <strong>Total Tasks:</strong>
            {" "}
            {result.tasks?.length || 0}
          </p>

        </div>

        <div className="summary-card">

          <h2>
            📋 Meeting Summary
          </h2>

          <p>
            {result.summary}
          </p>

        </div>

        <div className="task-section">

          <h2>
            ✅ Action Items
          </h2>

          {
            result.tasks?.length > 0
              ? result.tasks.map(
                  (task, index) => (

                    <div
                      key={index}
                      className={`task-card priority-${task.priority?.toLowerCase()}`}
                    >

                      <h3>
                        {task.task}
                      </h3>

                      <p>
                        <strong>
                          👤 Owner:
                        </strong>
                        {" "}
                        {task.owner}
                      </p>

                      <p>
                        <strong>
                          📅 Deadline:
                        </strong>
                        {" "}
                        {task.deadline_text}
                      </p>

                      <p>
                        <strong>
                          🗓 Date:
                        </strong>
                        {" "}
                        {task.deadline_date}
                      </p>

                      <p>
                        <strong>
                          🚨 Priority:
                        </strong>
                        {" "}
                        {task.priority}
                      </p>

                      <p>
                        <strong>
                          📌 Status:
                        </strong>
                        {" "}
                        {task.status}
                      </p>

                    </div>

                  )
                )
              : (
                <p>
                  No action items detected.
                </p>
              )
          }

        </div>

        <div className="transcript-card">

          <h2>
            📝 Transcript
          </h2>

          <textarea
            value={result.transcript}
            readOnly
            rows={10}
          />

        </div>

        <div className="action-buttons">

          <button
            className="calendar-btn"
            onClick={() =>
              navigate(
                `/calendar/${result.meeting_id}`
              )
            }
          >
            📅 View Calendar
          </button>

          
        </div>

      </div>

    )}

  </div>

</div>

);

}

export default UploadMeeting;

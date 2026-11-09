import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FaTrash,
  FaEdit,
  FaSave,
  FaTimes,
  FaEnvelope
} from "react-icons/fa";

import API from "../services/api";
import "./History.css";

function History() {

  const navigate = useNavigate();

  const [meetings, setMeetings] = useState([]);
  const [allMeetings, setAllMeetings] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [editedSummary, setEditedSummary] = useState("");
  // =========================
// Mail States
// =========================

const [showMailModal, setShowMailModal] =
  useState(false);

const [mailTo, setMailTo] =
  useState("");

const [mailSubject, setMailSubject] =
  useState("");

const [selectedMeeting, setSelectedMeeting] =
  useState(null);

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {

    try {

      const user =
        JSON.parse(
          localStorage.getItem("user")
        );

      const userId = user?.id;

      if (!userId) {

        alert("Please login first");
        return;

      }

      const response =
        await API.get(
          `/meetings/user/${userId}`
        );

      setMeetings(response.data);
      setAllMeetings(response.data);

    }
    catch (error) {

      console.log(error);

      alert("Failed to load meetings");

    }

  };

  const deleteMeeting = async (meetingId) => {

    const confirmDelete =
      window.confirm(
        "Are you sure you want to delete this meeting?"
      );

    if (!confirmDelete)
      return;

    try {

      await API.delete(
        `/meetings/${meetingId}`
      );

      setMeetings(prev =>
        prev.filter(
          meeting =>
            meeting.id !== meetingId
        )
      );

      setAllMeetings(prev =>
        prev.filter(
          meeting =>
            meeting.id !== meetingId
        )
      );

      alert(
        "Meeting deleted successfully"
      );

    }
    catch (error) {

      console.log(error);

      alert(
        "Failed to delete meeting"
      );

    }

  };

  const startEditing = (meeting) => {

    setEditingId(meeting.id);

    setEditedSummary(
      meeting.summary
    );

  };

  const cancelEditing = () => {

    setEditingId(null);

    setEditedSummary("");

  };

  const saveSummary = async (meetingId) => {

    try {

      await API.put(

        `/meetings/${meetingId}/summary`,

        {
          summary: editedSummary
        }

      );

      const updated =
        meetings.map(meeting =>

          meeting.id === meetingId

            ? {
                ...meeting,
                summary: editedSummary
              }

            : meeting

        );

      setMeetings(updated);

      setAllMeetings(updated);

      setEditingId(null);

      alert(
        "Summary updated successfully"
      );

    }
    catch (error) {

      console.log(error);

      alert(
        "Failed to update summary"
      );

    }

  };

  // =========================
// Open Mail Popup
// =========================

const openMailPopup = (meeting) => {

  setSelectedMeeting(meeting);

  setMailTo("");

  setMailSubject(
    `Meeting Summary - ${meeting.file_name}`
  );

  setShowMailModal(true);

};

// =========================
// Close Mail Popup
// =========================

const closeMailPopup = () => {

  setShowMailModal(false);

  setMailTo("");

  setMailSubject("");

  setSelectedMeeting(null);

};

// =========================
// Open Gmail
// =========================

const sendMail = () => {

  if (!mailTo.trim()) {

    alert("Please enter recipient email");

    return;

  }

  if (!mailSubject.trim()) {

    alert("Please enter subject");

    return;

  }

  const body = `Hello,

Please find the meeting summary below.

---------------------------------------

${selectedMeeting.summary}

---------------------------------------

Regards,
AI Meeting Notes System`;

  const gmailUrl =
    `https://mail.google.com/mail/?view=cm&fs=1` +
    `&to=${encodeURIComponent(mailTo)}` +
    `&su=${encodeURIComponent(mailSubject)}` +
    `&body=${encodeURIComponent(body)}`;

  window.open(
    gmailUrl,
    "_blank"
  );

  closeMailPopup();

};

  const searchByDate = () => {

    if (!selectedDate) {

      alert(
        "Please select a date"
      );

      return;

    }

    const filtered =
      allMeetings.filter(meeting => {

        const dbDate =
          new Date(
            meeting.created_at
          )
            .toISOString()
            .split("T")[0];

        return (
          dbDate === selectedDate
        );

      });

    setMeetings(filtered);

  };

  const showAll = () => {

    setMeetings(
      allMeetings
    );

    setSelectedDate("");

  };

  return (

    <div className="history-page">

      <div className="history-header">

        <h1>
          📂 Meeting History
        </h1>

        <p>
          View and manage your uploaded meetings
        </p>

      </div>

      <div className="search-bar">

        <input
          type="date"
          value={selectedDate}
          onChange={(e)=>
            setSelectedDate(
              e.target.value
            )
          }
        />

        <button
          onClick={searchByDate}
        >
          Search
        </button>

        <button
          className="all-btn"
          onClick={showAll}
        >
          Show All
        </button>

      </div>

      <div className="meeting-grid">

        {
          meetings.length === 0 ?

          (

            <h2 className="empty">

              No Meetings Found

            </h2>

          )

          :

          meetings.map(meeting => (

            <div

              key={meeting.id}

              className="meeting-card"

              onClick={() => {

                if (
                  editingId !== meeting.id
                ) {

                  navigate(
                    `/meeting/${meeting.id}`
                  );

                }

              }}

            >

              <button

                className="delete-btn"

                onClick={(e)=>{

                  e.stopPropagation();

                  deleteMeeting(
                    meeting.id
                  );

                }}

              >

                <FaTrash />

              </button>

              <h3>

                🎤 {meeting.file_name}

              </h3>

              <div className="summary-box"></div>
                            {
                editingId === meeting.id ?

                (

                  <>

                    <textarea

                      className="summary-editor"

                      value={editedSummary}

                      onClick={(e)=>
                        e.stopPropagation()
                      }

                      onChange={(e)=>
                        setEditedSummary(
                          e.target.value
                        )
                      }

                    />

                    <div className="summary-icons">

                      <FaSave

                        className="icon save-icon"

                        title="Save"

                        onClick={(e)=>{

                          e.stopPropagation();

                          saveSummary(
                            meeting.id
                          );

                        }}

                      />

                      <FaTimes

                        className="icon cancel-icon"

                        title="Cancel"

                        onClick={(e)=>{

                          e.stopPropagation();

                          cancelEditing();

                        }}

                      />

                    </div>

                  </>

                )

                :

                (

                  <div
                    className="meeting-summary"
                  >

                    <span>

                      {meeting.summary}

                    </span>

                    <FaEdit

                      className="icon edit-icon"

                      title="Edit Summary"

                      onClick={(e)=>{

                        e.stopPropagation();

                        startEditing(
                          meeting
                        );

                      }}

                    />

                  </div>

                )

              }

              {/* Mail Icon */}

<div className="card-actions">

  <FaEnvelope
    className="mail-icon"
    title="Send Summary"
    onClick={(e) => {

      e.stopPropagation();

      openMailPopup(meeting);

    }}
  />

</div>

              <span
                className="meeting-date"
              >

                {

                  new Date(
                    meeting.created_at
                  ).toLocaleString()

                }

              </span>

            </div>

          ))

        }

      </div>

      <div className="history-page"></div>
{/* ==========================
      Mail Popup
========================== */}

{
showMailModal && (

<div
className="mail-modal-overlay"
onClick={closeMailPopup}
>

<div
className="mail-modal"
onClick={(e)=>e.stopPropagation()}
>

<h2>
📧 Send Meeting Summary
</h2>

<label>

Recipient Email

</label>

<input

type="email"

placeholder="example@gmail.com"

value={mailTo}

onChange={(e)=>

setMailTo(

e.target.value

)

}

/>

<label>

Subject

</label>

<input

type="text"

value={mailSubject}

onChange={(e)=>

setMailSubject(

e.target.value

)

}

/>

<label>

Summary Preview

</label>

<textarea

readOnly

rows={10}

value={selectedMeeting?.summary || ""}

/>

<div className="mail-buttons">

<button

className="cancel-mail"

onClick={closeMailPopup}

>

Cancel

</button>

<button

className="send-mail"

onClick={sendMail}

>

Open Gmail

</button>

</div>

</div>

</div>

)
}
    </div>

  );

}

export default History;
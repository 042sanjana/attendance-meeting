import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

function Dashboard() {

  const navigate = useNavigate();

  const user =
    JSON.parse(
      localStorage.getItem("user")
    ) || {};

  const userName =
    user?.name || "User";

  const userEmail =
    user?.email || "";

  const logout = () => {

    localStorage.removeItem(
      "user"
    );

    navigate("/");

  };

  return (

    <div className="dashboard">

      <nav className="navbar">

        <div className="logo">
          AI Meeting Notes
        </div>

        <div className="right-section">

          <div className="profile">

            <div className="avatar">
              {user?.name
                ?.charAt(0)
                ?.toUpperCase()}
            </div>

            <div className="profile-info">

              <span className="name">
                {userName}
              </span>

              <span className="email">
                {userEmail}
              </span>

            </div>

          </div>

          <button
            className="logout-btn"
            onClick={logout}
          >
            Logout
          </button>

        </div>

      </nav>

      <div className="hero">

        <h1>
          AI Generated Meeting Notes
        </h1>

        <p>
          Upload office meeting recordings,
          generate transcripts, summaries,
          action items and deadline tracking.
        </p>

      </div>

      <div className="card-grid">

        <div
          className="dashboard-card"
          onClick={() =>
            navigate("/upload")
          }
        >
          <div className="icon">
            🎤
          </div>

          <h3>
            Upload Meeting
          </h3>

          <p>
            Upload MP3/WAV recordings.
          </p>

        </div>

        <div
          className="dashboard-card"
          onClick={() =>
            navigate("/history")
          }
        >
          <div className="icon">
            📂
          </div>

          <h3>
            Meeting History
          </h3>

          <p>
            View previous meetings.
          </p>

        </div>

        <div
          className="dashboard-card"
          onClick={() =>
            navigate("/calendar")
          }
        >
          <div className="icon">
            📅
          </div>

          <h3>
            Calendar
          </h3>

          <p>
            Track task deadlines.
          </p>

        </div>

        

        

      </div>

    </div>

  );
}

export default Dashboard;
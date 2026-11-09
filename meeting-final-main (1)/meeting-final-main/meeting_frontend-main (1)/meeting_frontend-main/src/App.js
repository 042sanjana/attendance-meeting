import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import UploadMeeting from "./pages/UploadMeeting";
import MeetingDetails from "./pages/MeetingDetails";
import History from "./pages/History";
import MeetingCard from "./components/MeetingCard";
import Navbar from "./components/Navbar";
import TaskTable from "./components/TaskTable";
import "./components/Navbar.css";
import "./pages/Login.css";
import "./pages/Register.css";
import "./pages/History.css";
import "./pages/UploadMeeting.css"
import TaskCalendar from "./components/TaskCalendar";
import  "./components/TaskCalendar.css";
import OutlookCalendar from "./pages/OutlookCalendar";

function App() {

  return (
    <BrowserRouter>

      <Routes>

        <Route path="/" element={<Login />} />

        <Route
          path="/register"
          element={<Register />}
        />
 <Route
  path="/calendar/:meetingId"
  element={<TaskCalendar />}
/>
<Route
  path="/tasks"
  element={<TaskTable />}
/>
<Route
  path="/outlook-calendar"
  element={<OutlookCalendar />}
/>

<Route
  path="/calendar"
  element={<TaskCalendar />}
/>
        
        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        <Route
          path="/upload"
          element={<UploadMeeting />}
        />

        <Route
          path="/history"
          element={<History />}
        />


        

        <Route
          path="/meeting/:id"
          element={<MeetingDetails />}
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;
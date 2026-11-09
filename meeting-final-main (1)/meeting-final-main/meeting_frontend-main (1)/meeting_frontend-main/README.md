# Attendance Dashboard + AI Meeting Notes

This project combines two complete applications into one integrated dashboard experience:

1. Employee Attendance Dashboard and ODC Tracker
2. AI Meeting Notes Generator with transcription, summarization, task extraction, and meeting management

The attendance dashboard remains the main application. The meeting notes module is added inside the same frontend shell as a separate feature set with its own user authentication and backend.

This makes the app useful for HR and operations teams that need both workforce attendance tracking and AI-assisted meeting management in one place.

## What this project does

### Attendance Dashboard
The attendance module helps organizations manage employee attendance using Excel uploads and live dashboard reporting.

Features include:
- Excel upload for attendance data
- employee management
- attendance summaries and KPI cards
- attendance analytics and charts
- ODC tracking
- employee detail views
- daily/period-based data analysis
- data reset functionality
- upload history and validation reports

### AI Meeting Notes
The meeting management module helps teams turn recorded meetings into structured output.

Features include:
- meeting account login and register
- secure meeting authentication using JWT tokens
- audio upload for meetings
- Whisper speech-to-text transcription
- BART-based summary generation
- automatic action item extraction
- task tracking and status updates
- meeting history view
- search by date
- summary editing
- task calendar
- export to calendar format

### Combined workflow
The final dashboard allows users to:
- manage attendance work as the primary business system
- access meeting management under a separate Meeting Management section
- login to the meeting account independently from the attendance dashboard
- upload meeting recordings and manage tasks without affecting the attendance database

## Key architecture decisions

- The attendance app remains the main dashboard application
- Meeting features are integrated into the same frontend but remain logically separate
- Attendance backend runs on port 8000
- Meeting backend runs on port 8001
- Attendance auth is separate from meeting auth
- Attendance database is separate from meeting database

## Project folders

The workspace contains these main folders:

```text
attendance-meeting/
├── dashboard-attendance-main/
│   ├── backend/
│   │   ├── app/
│   │   ├── requirements.txt
│   │   └── uploads/
│   ├── frontend/
│   │   ├── src/
│   │   ├── package.json
│   │   └── vite.config.js
│   ├── README.md
│   └── uploads/
│
├── meeting-final-main/
│   ├── meeting-backend-main/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── security.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── database/
│   │   └── uploads/
│   └── meeting_frontend-main/
│       ├── src/
│       ├── package.json
│       └── README.md
└── README.md
```

## Technologies used

### Frontend
- React
- Vite
- React Router
- Axios
- Recharts
- Lucide React

### Attendance backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pandas
- OpenPyXL

### Meeting backend
- Python
- FastAPI
- SQLite
- JWT authentication
- Whisper
- BART summarization
- task extraction logic

## Prerequisites

Before running the project, make sure you have:
- Python 3.10 or later
- Node.js 18 or later
- npm
- VS Code

Check the installed versions:

```bash
python --version
node --version
npm --version
```

## Run the project in VS Code

You need to run three components separately in different terminals:

1. Attendance backend
2. Meeting backend
3. Frontend

### 1) Start the Attendance backend

Open a terminal in VS Code and run:

```bash
cd "c:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\backend"
```

Then create a virtual environment:

Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the attendance backend:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

This runs the attendance API at:
- http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### 2) Start the Meeting backend

Open a second terminal in VS Code and run:

```bash
cd "c:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\meeting-final-main (1)\meeting-final-main\meeting-backend-main\meeting-backend-main"
```

Create a virtual environment:

Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the meeting backend:

```bash
python -m uvicorn main:app --reload --port 8001
```

This runs the meeting API at:
- http://localhost:8001
- Swagger docs: http://localhost:8001/docs

### 3) Start the frontend

Open a third terminal in VS Code and run:

```bash
cd "c:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\frontend"
```

Install frontend dependencies:

```bash
npm install
```

Start the dashboard frontend:

```bash
npm run dev -- --host 0.0.0.0
```

The frontend runs at:
- http://localhost:5173

## Full app URLs

After all three are running:

- Dashboard frontend: http://localhost:5173
- Attendance API: http://localhost:8000
- Meeting API: http://localhost:8001
- Attendance Swagger: http://localhost:8000/docs
- Meeting Swagger: http://localhost:8001/docs

## Meeting account flow

The meeting module includes its own authentication flow.

From the sidebar, users can:
- Login
- Register
- Logout

When the user logs in:
- meeting JWT token is stored
- meeting user details are stored
- protected meeting pages are unlocked
- unauthenticated users are redirected to the meeting login page

This is separate from the attendance dashboard authentication.

## Meeting features

Once logged in, the user can:
- upload meeting recordings
- view processing results
- inspect transcript summary
- review detected action items
- edit summary text
- review meeting history
- filter meetings by date
- manage tasks and statuses
- open the task calendar
- export tasks to a calendar file

## Attendance features

The core dashboard continues to include:
- employee records
- attendance data processing
- analytics and graphs
- dashboard cards and summaries
- ODC tracker
- Excel upload modal
- reset data feature
- upload history

## Important notes

- Attendance dashboard remains the main system
- Meeting notes is integrated into the same dashboard without replacing the attendance app
- Meeting data is kept separate from attendance data
- Meeting auth is kept separate from attendance auth
- The app is designed to run locally in VS Code with separate terminals

## Troubleshooting

### If Python packages are missing
```bash
pip install -r requirements.txt
```

### If Node packages are missing
```bash
npm install
```

### If the backend port is already in use
Use another free port when starting the server, for example:

```bash
python -m uvicorn app.main:app --reload --port 8000
python -m uvicorn main:app --reload --port 8001
```

### If meeting pages redirect to login
Login to the Meeting Account section first.

### If the frontend does not load
Check that the attendance backend, meeting backend, and frontend are all running.

## Summary

This project combines a modern attendance management dashboard with an AI-powered meeting workflow engine. It helps organizations:
- track workforce attendance
- monitor employee status and ODC activity
- generate meeting summaries with AI
- extract tasks automatically
- manage meetings and deadlines in a single integrated dashboard

It is a practical full-stack project that demonstrates integration of frontend, backend, database management, authentication, and AI-based processing.

## Quick start commands

```bash
# Attendance backend
cd "c:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\backend"
python -m uvicorn app.main:app --reload --port 8000

# Meeting backend
cd "c:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\meeting-final-main (1)\meeting-final-main\meeting-backend-main\meeting-backend-main"
python -m uvicorn main:app --reload --port 8001

# Frontend
cd "c:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\frontend"
npm install
npm run dev -- --host 0.0.0.0
```

Open the frontend at:

```text
http://localhost:5173
```

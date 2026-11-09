# Attendance Dashboard + AI Meeting Notes

A full-stack web application that combines:
- Employee Attendance Dashboard and ODC Tracker
- AI Meeting Notes processing with audio upload, transcript generation, meeting summaries, task extraction, history tracking, and task calendar management

This project keeps the existing attendance dashboard as the main application while integrating the Meeting Notes functionality as a separate module with its own protected auth flow and dedicated backend.

## Features

### Attendance Dashboard
- Employee attendance dashboard
- Upload Excel attendance data
- Attendance analytics and charts
- Employee management
- ODC tracker
- Dashboard refresh and reset support
- Existing attendance UI and backend remain intact

### AI Meeting Notes
- Audio upload (`.wav`, `.mp3`, `.m4a`)
- Whisper speech-to-text transcription
- BART summary generation
- Automatic task extraction
- Meeting history
- Meeting task tracking
- Task calendar export and updates
- Separate meeting authentication
- Meeting account login/register/logout

## Project Structure

```text
attendance-meeting/
├── dashboard-attendance-main/
│   ├── README.md
│   ├── backend/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   ├── database.py
│   │   │   ├── excel_processor.py
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── odc_tracker.py
│   │   │   └── schemas.py
│   │   ├── generate_sample_data.py
│   │   ├── requirements.txt
│   │   └── uploads/
│   ├── frontend/
│   │   ├── package.json
│   │   ├── vite.config.js
│   │   ├── index.html
│   │   └── src/
│   │       ├── App.jsx
│   │       ├── api.js
│   │       ├── index.css
│   │       ├── main.jsx
│   │       ├── meetingApi.js
│   │       ├── components/
│   │       └── pages/
│   └── uploads/
│
├── meeting-final-main/
│   └── meeting-backend-main/
│       ├── main.py
│       ├── requirements.txt
│       ├── security.py
│       ├── database/
│       ├── routes/
│       ├── services/
│       └── uploads/
└── README.md (this file)
```

## Tech Stack

### Attendance Dashboard
- React + Vite
- FastAPI
- SQLAlchemy
- SQLite
- Recharts
- Lucide React

### Meeting Notes
- React + Vite (integrated into dashboard frontend)
- FastAPI
- SQLite
- Whisper
- BART summarizer
- JWT authentication
- Task extraction and date parsing

## Requirements

- Python 3.10+
- Node.js 18+
- npm
- Git

## Installation

### 1) Clone the project

```bash
git clone <repository-url>
cd attendance-meeting
dashboard-attendance-main
```

### 2) Install attendance backend dependencies

```bash
cd backend
python -m venv venv
```

Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Windows Command Prompt:
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

macOS/Linux:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3) Start attendance backend

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Attendance backend runs at:
- http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 4) Install meeting backend dependencies

Open a second terminal and run:

```bash
cd ..\meeting-final-main\meeting-backend-main\meeting-backend-main
python -m venv venv
```

Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Windows Command Prompt:
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

macOS/Linux:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 5) Start meeting backend

```bash
python -m uvicorn main:app --reload --port 8001
```

Meeting backend runs at:
- http://localhost:8001
- Swagger UI: http://localhost:8001/docs

### 6) Install frontend dependencies

Open a third terminal and run:

```bash
cd ..\dashboard-attendance-main\frontend
npm install
```

### 7) Start the dashboard frontend

```bash
npm run dev -- --host 0.0.0.0
```

Frontend runs at:
- http://localhost:5173

## Running the Full Application

You must keep all three services running at the same time:

1. Attendance backend on port 8000
2. Meeting backend on port 8001
3. Dashboard frontend on port 5173

## Meeting Notes Login / Registration

The meeting notes module has its own authentication system and JWT token storage. This is separate from the attendance dashboard login system.

Use the Meeting Account section in the sidebar to:
- Login
- Register
- Logout

After successful login or registration:
- the meeting JWT token is stored locally
- meeting user details are stored locally
- protected meeting pages are available
- unauthenticated users are redirected to the meeting login page

## Important Notes

- Attendance dashboard app remains the main application
- Meeting functionality is integrated into the same dashboard frontend
- Meeting backend uses a separate database from the attendance backend
- Attendance authentication remains separate from meeting authentication
- Do not delete or overwrite working attendance features

## Useful Commands

### Attendance backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Meeting backend
```bash
cd meeting-final-main/meeting-backend-main/meeting-backend-main
python -m uvicorn main:app --reload --port 8001
```

### Frontend
```bash
cd dashboard-attendance-main/frontend
npm run dev -- --host 0.0.0.0
```

## Troubleshooting

### If dependencies are missing
```bash
pip install -r requirements.txt
npm install
```

### If ports are already in use
Change the port in the uvicorn command:
```bash
python -m uvicorn app.main:app --reload --port 8000
python -m uvicorn main:app --reload --port 8001
```

### If frontend does not load
Ensure the backend services are running before opening the app in the browser.

## License

This project is intended for internal use and development.

<<<<<<< HEAD
# Attendance Dashboard + Organization Hierarchy

This project contains two related modules:

1. Attendance Dashboard – employee attendance tracking, analytics, ODC tracker, and meeting management
2. Organization Hierarchy – employee reporting tree, manager relationships, and org chart visualization
=======
# Attendance Dashboard + Meeting Notes + Hierarchy

A complete employee management and productivity platform that combines:

- Attendance dashboard for employee tracking and analytics
- ODC tracking and performance monitoring
- AI-powered meeting notes with audio upload, transcription, summary generation, and task extraction
- Organization hierarchy management for manager and team structure

This project brings multiple modules together into one workspace so the main dashboard can be used as the central interface while the meeting notes and hierarchy features remain available as extensions of the same business workflow.

## Project Description

This solution is designed for HR, operations, and management teams who need an integrated view of:

- employee attendance and working patterns
- organizational structure and reporting lines
- meeting outcomes and action items
- task tracking from discussions and review meetings

The project includes:

1. Attendance Dashboard Module
   - employee management
   - CSV/Excel upload support
   - attendance analytics and charts
   - ODC tracker
   - dashboard overview screens

2. Meeting Notes Module
   - audio upload for meeting recordings
   - speech-to-text transcription using Whisper
   - AI summary generation using BART
   - automatic task extraction
   - meeting history and task calendar management
   - login and protected routes for meeting users

3. Organization Hierarchy Module
   - employee reporting hierarchy
   - manager/subordinate relationships
   - org chart style data display
   - integrated hierarchy page in the main dashboard
>>>>>>> c2af2e1 (updated)

The organization hierarchy module is also integrated into the dashboard as a separate page in the sidebar.

<<<<<<< HEAD
## Project structure

```text
attendance-meeting/
├── dashboard-attendance-main/
│   ├── README.md
│   ├── backend/
│   │   └── app/
│   └── frontend/
│       └── src/
├── organization-hierachy-main/
│   ├── README.md
│   ├── organization heirachy/
│   │   ├── backend/
│   │   └── ...
│   └── org frontend/
│       └── org/
└── meeting-final-main/
    └── ...
=======
### Attendance Dashboard
- Employee attendance tracking
- Upload attendance Excel files
- Analytics and charts
- Employee add/edit/delete support
- Dashboard summaries and trend analysis
- ODC tracker and workforce monitoring

### Meeting Notes
- Audio upload in common formats like `.wav`, `.mp3`, and `.m4a`
- Speech-to-text transcription
- AI summary creation
- Automatic task extraction from meeting discussions
- Meeting history tracking
- Task management and calendar coordination
- Authentication for meeting users

### Organization Hierarchy
- Employee reporting structure
- Manager/team relationships
- Data organization by department or reporting line
- Dashboard integration for HR workflows

## Tech Stack

### Frontend
- React
- Vite
- JavaScript / JSX
- CSS
- Recharts
- Axios

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

### AI / Meeting Features
- Whisper for transcription
- BART for summaries
- JWT-based secure auth

## Project Structure

```text
attendance-meeting/
├── README.md
├── dashboard-attendance-main (1)/
│   └── dashboard-attendance-main/
│       ├── backend/
│       │   ├── app/
│       │   ├── requirements.txt
│       │   ├── generate_sample_data.py
│       │   └── uploads/
│       ├── frontend/
│       │   ├── package.json
│       │   ├── vite.config.js
│       │   └── src/
│       └── uploads/
├── meeting-final-main (1)/
│   └── meeting-final-main/
│       ├── meeting-backend-main/
│       │   ├── main.py
│       │   ├── requirements.txt
│       │   ├── security.py
│       │   ├── database/
│       │   ├── routes/
│       │   ├── services/
│       │   └── uploads/
│       └── meeting_frontend-main/
│           └── ...
├── organization-hierachy-main/
│   ├── org frontend/
│   ├── organization heirachy/
│   └── README.md
└── .git/
>>>>>>> c2af2e1 (updated)
```

## Prerequisites

<<<<<<< HEAD
Install the following first:
=======
Install the following before running the project:
>>>>>>> c2af2e1 (updated)

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- Git

<<<<<<< HEAD
Check versions:
=======
Verify that everything is installed:
>>>>>>> c2af2e1 (updated)

```bash
python --version
node -v
npm -v
```

<<<<<<< HEAD
## 1) Run the Attendance Dashboard

### Backend

Open a terminal and run:

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will run at:

- http://localhost:8000
- API docs: http://localhost:8000/docs

### Frontend
=======
## Quick Start

The project has multiple services. Run them in separate terminals.

Required for the main dashboard experience:

1. Attendance Dashboard Backend
2. Attendance Dashboard Frontend
3. Meeting Notes Backend

Optional:

- Standalone Organization Hierarchy App

## 1) Start the Attendance Dashboard Backend

Open a terminal in the project root and run:

```bash
cd "dashboard-attendance-main (1)\dashboard-attendance-main\backend"
python -m venv .venv
```

### Activate virtual environment

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The dashboard backend will run at:

- http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## 2) Start the Attendance Dashboard Frontend
>>>>>>> c2af2e1 (updated)

Open a second terminal and run:

```bash
<<<<<<< HEAD
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\frontend"
npm install
npm run dev -- --host 0.0.0.0
```

The dashboard will run at:

- http://localhost:5173

The integrated Organization Hierarchy page is available from the sidebar inside this dashboard.

## 2) Run the Organization Hierarchy Module (Standalone)

If you want to run the original hierarchy project separately, use the following commands.

### Backend

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\organization-hierachy-main\organization heirachy\backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

This backend runs at:

- http://localhost:8000

### Frontend

Open another terminal and run:

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\organization-hierachy-main\org frontend\org"
npm install
npm start
```

The standalone hierarchy UI runs at:

- http://localhost:3000

## 3) Local development flow

For the full dashboard experience, run these together:

1. Dashboard backend on port 8000
2. Dashboard frontend on port 5173
3. Keep the hierarchy page from the sidebar and upload Excel files from the dashboard UI

If you want the original standalone hierarchy app, run:

1. Organization hierarchy backend on port 8000
2. Organization hierarchy frontend on port 3000

## Important notes

- The dashboard backend and the standalone hierarchy backend both use FastAPI and can run on the same port only one at a time.
- The integrated dashboard page is the recommended way to use the hierarchy feature inside the HR dashboard.
- If you run the standalone org app and dashboard app together, use different ports or stop one before starting the other.

## Useful commands summary

### Dashboard backend

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\backend"
.venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Dashboard frontend

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\dashboard-attendance-main (1)\dashboard-attendance-main\frontend"
npm install
npm run dev -- --host 0.0.0.0
=======
cd "dashboard-attendance-main (1)\dashboard-attendance-main\frontend"
npm install
npm run dev -- --host 0.0.0.0
```

The dashboard frontend will run at:

- http://localhost:5173

## 3) Start the Meeting Notes Backend

Open a third terminal and run:

```bash
cd "meeting-final-main (1)\meeting-final-main\meeting-backend-main\meeting-backend-main"
python -m venv .venv
```

### Activate virtual environment

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the meeting backend:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

The meeting backend will run at:

- http://localhost:8001
- Swagger docs: http://localhost:8001/docs

## 4) Run the Organization Hierarchy Module

The hierarchy module is also available as part of the main dashboard. If you want to run the standalone hierarchy app separately, use the following commands.

### Hierarchy Backend

```bash
cd "organization-hierachy-main\organization heirachy\backend"
python -m venv .venv
```

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Hierarchy Frontend

Open a new terminal and run:

```bash
cd "organization-hierachy-main\org frontend\org"
npm install
npm start
```

The standalone hierarchy frontend runs at:

- http://localhost:3000

## Full Application Run Summary

For the main integrated experience, keep these running together:

1. Dashboard backend on http://localhost:8000
2. Meeting backend on http://localhost:8001
3. Dashboard frontend on http://localhost:5173

This gives you:

- attendance dashboard
- meeting notes module
- hierarchy feature inside the dashboard

## Important Notes

- The attendance dashboard and meeting notes use separate backend services.
- The meeting notes login is separate from the dashboard login system.
- If you run the standalone hierarchy app and the dashboard app together, do not use the same port at the same time.
- Use separate terminals for each backend and frontend service.
- Do not stop the dashboard backend or frontend during normal use unless you are restarting the app.

## Environment Setup Commands (Windows)

### Dashboard backend

```powershell
cd "dashboard-attendance-main (1)\dashboard-attendance-main\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Dashboard frontend

```powershell
cd "dashboard-attendance-main (1)\dashboard-attendance-main\frontend"
npm install
npm run dev -- --host 0.0.0.0
```

### Meeting backend

```powershell
cd "meeting-final-main (1)\meeting-final-main\meeting-backend-main\meeting-backend-main"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Hierarchy backend

```powershell
cd "organization-hierachy-main\organization heirachy\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Hierarchy frontend

```powershell
cd "organization-hierachy-main\org frontend\org"
npm install
npm start
>>>>>>> c2af2e1 (updated)
```

### Organization hierarchy backend

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\organization-hierachy-main\organization heirachy\backend"
.venv\Scripts\activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Organization hierarchy frontend

```bash
cd "C:\Users\sanjanavinu.kannan\Downloads\attendance-meeting\organization-hierachy-main\org frontend\org"
npm install
npm start
```

## Troubleshooting

<<<<<<< HEAD
### If pip install fails
=======
### If `pip install` fails
>>>>>>> c2af2e1 (updated)

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

<<<<<<< HEAD
### If npm install fails
=======
### If `npm install` fails
>>>>>>> c2af2e1 (updated)

```bash
npm cache clean --force
npm install
```

### If a port is already in use

Change the port in the command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

<<<<<<< HEAD
or update the frontend dev server port if needed.

## Final note

Use the dashboard UI as the main application for daily work. The standalone organization hierarchy project is included as a separate module and can also be run independently when needed.
=======
### If the frontend does not open

Check whether the app is still running in the terminal and confirm the correct port:

- dashboard: http://localhost:5173
- hierarchy standalone: http://localhost:3000

## Usage Guide

After starting the services:

1. Open the dashboard frontend in the browser.
2. Use the attendance dashboard to upload employee attendance data.
3. Access meeting features from the integrated dashboard.
4. Log in/register to the meeting module if required.
5. Use the hierarchy panel from the dashboard sidebar if needed.

## Final Notes

This project is a practical HR and operations dashboard that brings together attendance, hierarchy, and AI meeting note management in a single workspace. It is designed to help teams monitor workforce activity, manage reporting lines, and convert meeting conversations into actionable tasks.

For day-to-day work, the main dashboard is the recommended interface. The standalone hierarchy project is included as an optional module when a separate org chart app is needed.
>>>>>>> c2af2e1 (updated)

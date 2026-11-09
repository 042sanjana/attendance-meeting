# Attendance Dashboard + Organization Hierarchy

This project contains two related modules:

1. Attendance Dashboard – employee attendance tracking, analytics, ODC tracker, and meeting management
2. Organization Hierarchy – employee reporting tree, manager relationships, and org chart visualization

The organization hierarchy module is also integrated into the dashboard as a separate page in the sidebar.

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
```

## Prerequisites

Install the following first:

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- Git

Check versions:

```bash
python --version
node -v
npm -v
```

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

Open a second terminal and run:

```bash
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

### If pip install fails

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### If npm install fails

```bash
npm cache clean --force
npm install
```

### If a port is already in use

Change the port in the command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

or update the frontend dev server port if needed.

## Final note

Use the dashboard UI as the main application for daily work. The standalone organization hierarchy project is included as a separate module and can also be run independently when needed.

# Organization Hierarchy Visualization System

## Overview

The **Organization Hierarchy Visualization System** is a web-based application that transforms employee data stored in an Excel file into an interactive organizational chart.

The application reads employee information from an Excel spreadsheet, stores it in a SQLite database, automatically builds reporting relationships, and displays them in a graphical hierarchy using **React Flow**. Users can also perform CRUD (Create, Read, Update, Delete) operations on employee records without modifying the original Excel file.

---

# Features

* 📂 Upload employee data from an Excel file
* 🌳 Automatic organization hierarchy generation
* 👥 Interactive organization chart
* 🔍 Search employees by name or employee ID
* 👤 View employee details
* ➕ Add new employees
* ✏️ Update employee information
* ❌ Delete employee records
* 💾 SQLite database storage
* 🖼️ Gender-based profile avatars
* 📱 Responsive user interface

---

# Technologies Used

## Frontend

* React.js
* React Flow
* Dagre
* Axios
* HTML
* CSS
* JavaScript

## Backend

* FastAPI
* Python 3.14
* Pandas
* SQLite

---

# How It Works

1. Upload an Excel file containing employee information.
2. The backend reads the Excel file using Pandas.
3. Employee data is stored in a SQLite database.
4. The system identifies reporting relationships using Employee ID and Manager ID.
5. A hierarchical tree is generated automatically.
6. React Flow displays the hierarchy as an interactive organizational chart.
7. Users can search, view, add, update, or delete employee records through the web interface.

---

# Project Structure

```text
organization-backend/
│
├── app.py
├── database/
├── routes/
├── services/
├── uploads/
├── requirements.txt
└── ...

organization-frontend/
│
├── src/
├── public/
├── package.json
└── ...
```

---

# Prerequisites

Install the following software before running the project:

* Python 3.14
* Node.js
* Visual Studio Code
* Git

---

# Verify Installation

Open Command Prompt or Terminal and run:

```bash
python --version
node -v
npm -v
```

---

# Backend Setup

## Step 1: Clone the Backend Repository

```bash
git clone https://github.com/042sanjana/organization-hierachy.git
```

---

## Step 2: Navigate to the Project

```bash
cd organization-hierarchy
```

---

## BACKEND SETUP
##Navigate to backend
'''bash
cd "organization heirachy"
cd "organization heirachy/backend"
```

---

## Step 4: Create a Virtual Environment

```bash
python -m venv venv
```

---

## Step 5: Activate the Virtual Environment

### Windows (Command Prompt)

```bash
venv\Scripts\activate
```



## Step 6: Install Dependencies

If **requirements.txt** is available:

```bash
pip install -r requirements.txt
```

---

## Step 7: Run the Backend

```bash
uvicorn app:app --reload
```

If everything is configured correctly, you should see:

```text
Uvicorn running on http://127.0.0.1:8000
```

---

# API Documentation

FastAPI automatically generates Swagger documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

---

# Frontend Setup



## Step 1: Navigate to the frontend Project

```bash
cd organization-hierarchy
cd "org frontend/org"
```

---

## Step 3: Install Dependencies

```bash
npm install
```

---

## Step 4: Start the React Application

```bash
npm start
```

The application will open in your browser at:

```text
http://localhost:3000
```

(or the port shown in your terminal)

---

# Application Workflow

1. Upload an Excel file containing employee information.
2. The backend reads and validates the Excel data.
3. Employee records are stored in SQLite.
4. The reporting hierarchy is generated automatically.
5. React Flow displays the hierarchy in a graphical tree.
6. Users can:

   * Search employees
   * View employee details
   * Add new employees
   * Update employee information
   * Delete employee records
   * Explore reporting relationships

---

# Technologies and Their Purpose

| Technology | Purpose                        |
| ---------- | ------------------------------ |
| React.js   | Frontend user interface        |
| React Flow | Interactive organization chart |
| Dagre      | Automatic node layout          |
| Axios      | Frontend-backend communication |
| FastAPI    | Backend REST API               |
| Pandas     | Read and process Excel files   |
| SQLite     | Database storage               |
| Python     | Backend development            |

---

# Advantages

* Clear visualization of reporting relationships
* Eliminates manual navigation through Excel sheets
* Interactive organization chart
* Easy employee management through CRUD operations
* Automatic hierarchy generation
* Clean node layout using Dagre
* Persistent database storage
* Scalable for medium to large organizations

---

# Limitations

* Initial employee data must be uploaded from an Excel file.
* Supports one organization at a time.
* Uses basic authentication.
* SQLite is best suited for small to medium-sized applications.
* Default profile avatars only.
* No audit history for record modifications.

---

# Future Enhancements

* Multi-organization support
* Employee profile photo uploads
* Department-wise hierarchy views
* Export hierarchy to PDF, PNG, and Excel
* Manager notifications
* PostgreSQL/MySQL database support
* Analytics dashboard
* Role-Based Access Control (RBAC)
* Drag-and-drop hierarchy management
* Real-time updates using WebSockets

---

# Contributors

**Sanjana Vinu**

---

# License

This project is developed for educational and learning purposes.

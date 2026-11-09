import os
import sqlite3
from typing import Any, Dict, List
import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(DB_DIR, "organization_hierarchy.db")

router = APIRouter(prefix="/api/org", tags=["organization-hierarchy"])

MALE_PROFILE = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
FEMALE_PROFILE = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            employee_number TEXT PRIMARY KEY,
            employee_name TEXT,
            designation TEXT,
            manager_id TEXT,
            date_of_joining TEXT,
            email_address TEXT,
            location TEXT,
            resource_country TEXT,
            resource_onsite_offshore TEXT,
            onsite_offshore_nearshore TEXT,
            client_location TEXT,
            emp_work_location TEXT,
            from_date TEXT,
            gender TEXT,
            profile TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def normalize(value: Any) -> str | None:
    if pd.isna(value):
        return None

    value = str(value).strip()
    if value == "" or value.lower() == "nan":
        return None

    try:
        return str(int(float(value)))
    except Exception:
        return value


def clear_database() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees")
    conn.commit()
    conn.close()


def insert_employee(employee: Dict[str, Any]) -> None:
    employee_number = normalize(employee.get("employee_number") or employee.get("EMPLOYEE NUMBER"))
    manager_id = normalize(employee.get("manager_id") or employee.get("MANAGER ID"))
    gender = str(employee.get("gender") or employee.get("GENDER") or "").strip().lower()
    profile = FEMALE_PROFILE if gender == "female" else MALE_PROFILE

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO employees (
            employee_number,
            employee_name,
            designation,
            manager_id,
            date_of_joining,
            email_address,
            location,
            resource_country,
            resource_onsite_offshore,
            onsite_offshore_nearshore,
            client_location,
            emp_work_location,
            from_date,
            gender,
            profile
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            employee_number,
            employee.get("employee_name") or employee.get("EMPLOYEE NAME"),
            employee.get("designation") or employee.get("DESIGNATION"),
            manager_id,
            employee.get("date_of_joining") or employee.get("DATE OF JOINING"),
            employee.get("email_address") or employee.get("EMAIL ADDRESS"),
            employee.get("location") or employee.get("LOCATION"),
            employee.get("resource_country") or employee.get("RESOURCE COUNTRY"),
            employee.get("resource_onsite_offshore") or employee.get("RESOURCE ONSITE OFFSHORE"),
            employee.get("onsite_offshore_nearshore") or employee.get("ONSITE OFFSHORE NEARSHORE"),
            employee.get("client_location") or employee.get("CLIENT LOCATION"),
            employee.get("emp_work_location") or employee.get("EMP_WORK_LOCATION"),
            employee.get("from_date") or employee.get("FROM_DATE"),
            employee.get("gender") or employee.get("GENDER"),
            employee.get("profile") or employee.get("PROFILE") or profile,
        ),
    )
    conn.commit()
    conn.close()


def get_all_employees() -> List[sqlite3.Row]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM employees ORDER BY employee_name").fetchall()
    conn.close()
    return rows


def build_hierarchy(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes: Dict[str, Dict[str, Any]] = {}
    roots: List[Dict[str, Any]] = []

    for row in data:
        employee = dict(row)
        emp_id = normalize(employee.get("employee_number") or employee.get("EMPLOYEE NUMBER"))
        manager_id = normalize(employee.get("manager_id") or employee.get("MANAGER ID"))
        gender = str(employee.get("gender") or employee.get("GENDER") or "").lower()
        profile = FEMALE_PROFILE if gender == "female" else MALE_PROFILE

        frontend_employee = {
            "EMPLOYEE NUMBER": emp_id,
            "EMPLOYEE NAME": employee.get("employee_name") or employee.get("EMPLOYEE NAME"),
            "DESIGNATION": employee.get("designation") or employee.get("DESIGNATION"),
            "MANAGER ID": manager_id,
            "DATE OF JOINING": employee.get("date_of_joining") or employee.get("DATE OF JOINING"),
            "EMAIL ADDRESS": employee.get("email_address") or employee.get("EMAIL ADDRESS"),
            "LOCATION": employee.get("location") or employee.get("LOCATION"),
            "RESOURCE COUNTRY": employee.get("resource_country") or employee.get("RESOURCE COUNTRY"),
            "RESOURCE ONSITE OFFSHORE": employee.get("resource_onsite_offshore") or employee.get("RESOURCE ONSITE OFFSHORE"),
            "ONSITE OFFSHORE NEARSHORE": employee.get("onsite_offshore_nearshore") or employee.get("ONSITE OFFSHORE NEARSHORE"),
            "CLIENT LOCATION": employee.get("client_location") or employee.get("CLIENT LOCATION"),
            "EMP_WORK_LOCATION": employee.get("emp_work_location") or employee.get("EMP_WORK_LOCATION"),
            "FROM_DATE": employee.get("from_date") or employee.get("FROM_DATE"),
            "GENDER": employee.get("gender") or employee.get("GENDER"),
            "PROFILE": employee.get("profile") or employee.get("PROFILE") or profile,
        }

        nodes[emp_id] = {
            "id": emp_id,
            "name": frontend_employee["EMPLOYEE NAME"],
            "designation": frontend_employee["DESIGNATION"],
            "employee": frontend_employee,
            "children": [],
        }

    for row in data:
        employee = dict(row)
        emp_id = normalize(employee.get("employee_number") or employee.get("EMPLOYEE NUMBER"))
        manager_id = normalize(employee.get("manager_id") or employee.get("MANAGER ID"))

        if manager_id is None:
            roots.append(nodes[emp_id])
        elif manager_id in nodes:
            nodes[manager_id]["children"].append(nodes[emp_id])
        else:
            roots.append(nodes[emp_id])

    return roots


def get_hierarchy() -> List[Dict[str, Any]]:
    employees = [dict(emp) for emp in get_all_employees()]
    return build_hierarchy(employees)


def search_employee(search_text: str) -> List[Dict[str, Any]]:
    hierarchy = get_hierarchy()
    results: List[Dict[str, Any]] = []
    stack = hierarchy.copy()
    search = str(search_text).strip().lower()

    while stack:
        node = stack.pop()
        employee = node["employee"]
        emp_name = str(employee.get("EMPLOYEE NAME", "")).lower()
        emp_number = str(employee.get("EMPLOYEE NUMBER", "")).lower()

        if search in emp_name or search in emp_number:
            results.append(employee)

        stack.extend(node["children"])

    return results


def add_employee(employee: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized = dict(employee)
    normalized["EMPLOYEE NUMBER"] = employee.get("EMPLOYEE NUMBER") or employee.get("employee_number")
    normalized["EMPLOYEE NAME"] = employee.get("EMPLOYEE NAME") or employee.get("employee_name")
    normalized["DESIGNATION"] = employee.get("DESIGNATION") or employee.get("designation")
    normalized["MANAGER ID"] = employee.get("MANAGER ID") or employee.get("manager_id")
    normalized["GENDER"] = employee.get("GENDER") or employee.get("gender")
    insert_employee(normalized)
    return get_hierarchy()


def update_employee(employee_number: str, employee: Dict[str, Any]) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE employees SET
            employee_name = ?,
            designation = ?,
            manager_id = ?,
            date_of_joining = ?,
            email_address = ?,
            location = ?,
            resource_country = ?,
            resource_onsite_offshore = ?,
            onsite_offshore_nearshore = ?,
            client_location = ?,
            emp_work_location = ?,
            from_date = ?,
            gender = ?,
            profile = ?
        WHERE employee_number = ?
        """,
        (
            employee.get("EMPLOYEE NAME") or employee.get("employee_name"),
            employee.get("DESIGNATION") or employee.get("designation"),
            normalize(employee.get("MANAGER ID") or employee.get("manager_id")),
            employee.get("DATE OF JOINING") or employee.get("date_of_joining"),
            employee.get("EMAIL ADDRESS") or employee.get("email_address"),
            employee.get("LOCATION") or employee.get("location"),
            employee.get("RESOURCE COUNTRY") or employee.get("resource_country"),
            employee.get("RESOURCE ONSITE OFFSHORE") or employee.get("resource_onsite_offshore"),
            employee.get("ONSITE OFFSHORE NEARSHORE") or employee.get("onsite_offshore_nearshore"),
            employee.get("CLIENT LOCATION") or employee.get("client_location"),
            employee.get("EMP_WORK_LOCATION") or employee.get("emp_work_location"),
            employee.get("FROM_DATE") or employee.get("from_date"),
            employee.get("GENDER") or employee.get("gender"),
            employee.get("PROFILE") or employee.get("profile") or (FEMALE_PROFILE if str(employee.get("GENDER") or employee.get("gender") or "").lower() == "female" else MALE_PROFILE),
            employee_number,
        ),
    )
    conn.commit()
    conn.close()
    return get_hierarchy()


def delete_employee(employee_number: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE employee_number = ?", (employee_number,))
    conn.commit()
    conn.close()
    return {"status": "success", "deleted_employee_number": employee_number}


@router.post("/upload")
@router.post("/upload-org")
async def upload_org(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are allowed.")

    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        df = pd.read_excel(io.BytesIO(file_content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read Excel file: {exc}") from exc

    df.columns = [str(col).strip() for col in df.columns]
    employees = df.to_dict(orient="records")

    clear_database()
    for employee in employees:
        row = dict(employee)
        row["PROFILE"] = FEMALE_PROFILE if str(row.get("GENDER") or row.get("gender") or "").strip().lower() == "female" else MALE_PROFILE
        insert_employee(row)

    return get_hierarchy()


@router.get("/hierarchy")
def hierarchy():
    return get_hierarchy()


@router.get("/employees/search/{search_text}")
def search(search_text: str):
    return search_employee(search_text)


@router.post("/employees")
def create_employee(employee: Dict[str, Any]):
    return add_employee(employee)


@router.put("/employees/{employee_number}")
def edit_employee(employee_number: str, employee: Dict[str, Any]):
    return update_employee(employee_number, employee)


@router.delete("/employees/{employee_number}")
def remove_employee(employee_number: str):
    return delete_employee(employee_number)


@router.get("/employees/{employee_number}")
def get_employee(employee_number: str):
    hierarchy = get_hierarchy()
    stack = hierarchy.copy()

    while stack:
        node = stack.pop()
        if str(node["employee"].get("EMPLOYEE NUMBER")) == str(employee_number):
            return node["employee"]
        stack.extend(node["children"])

    raise HTTPException(status_code=404, detail="Employee Not Found")


@router.get("/employees")
def get_all():
    hierarchy = get_hierarchy()
    employees: List[Dict[str, Any]] = []
    stack = hierarchy.copy()

    while stack:
        node = stack.pop()
        employees.append(node["employee"])
        stack.extend(node["children"])

    return employees


create_tables()

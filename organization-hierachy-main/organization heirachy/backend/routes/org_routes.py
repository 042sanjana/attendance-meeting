from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd

from database.db import (
    clear_database,
    insert_employee
)

from services.org_service import (
    build_hierarchy,
    get_hierarchy,
    add_employee,
    update_employee,
    delete_employee,
    search_employee
)

router = APIRouter()

MALE_PROFILE = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
FEMALE_PROFILE = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"


# ======================================================
# Upload Excel
# ======================================================

@router.post("/upload-org")
async def upload_org(file: UploadFile = File(...)):

    df = pd.read_excel(file.file)

    df.columns = df.columns.str.strip()

    employees = df.to_dict(orient="records")

    clear_database()

    for employee in employees:

        gender = str(
            employee.get("GENDER", "")
        ).strip().lower()

        employee["PROFILE"] = (
            FEMALE_PROFILE
            if gender == "female"
            else MALE_PROFILE
        )

        insert_employee(employee)

    return get_hierarchy()


# ======================================================
# Get Hierarchy
# ======================================================

@router.get("/hierarchy")
def hierarchy():

    return get_hierarchy()


# ======================================================
# Search Employee (Name or Employee Number)
# ======================================================

@router.get("/employees/search/{search_text}")
def search(search_text: str):

    return search_employee(search_text)


# ======================================================
# Add Employee
# ======================================================

@router.post("/employees")
def create_employee(employee: dict):

    return add_employee(employee)


# ======================================================
# Update Employee
# ======================================================

@router.put("/employees/{employee_number}")
def edit_employee(
    employee_number: str,
    employee: dict
):

    return update_employee(
        employee_number,
        employee
    )


# ======================================================
# Delete Employee
# ======================================================

@router.delete("/employees/{employee_number}")
def remove_employee(employee_number: str):

    return delete_employee(employee_number)


# ======================================================
# Get One Employee
# ======================================================

@router.get("/employees/{employee_number}")
def get_employee(employee_number: str):

    hierarchy = get_hierarchy()

    stack = hierarchy.copy()

    while stack:

        node = stack.pop()

        if str(
            node["employee"]["EMPLOYEE NUMBER"]
        ) == str(employee_number):

            return node["employee"]

        stack.extend(node["children"])

    raise HTTPException(
        status_code=404,
        detail="Employee Not Found"
    )


# ======================================================
# Get All Employees (Flat List)
# ======================================================

@router.get("/employees")
def get_all():

    hierarchy = get_hierarchy()

    employees = []

    stack = hierarchy.copy()

    while stack:

        node = stack.pop()

        employees.append(
            node["employee"]
        )

        stack.extend(
            node["children"]
        )

    return employees
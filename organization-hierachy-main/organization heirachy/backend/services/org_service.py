import pandas as pd

from database.db import (
    get_connection,
    insert_employee,
    get_all_employees
)

MALE_PROFILE = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
FEMALE_PROFILE = "https://cdn-icons-png.flaticon.com/512/6997/6997662.png"


# ==================================================
# NORMALIZE
# ==================================================

def normalize(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return None

    try:
        return str(int(float(value)))
    except:
        return value


# ==================================================
# BUILD HIERARCHY
# ==================================================

def build_hierarchy(data):

    nodes = {}
    roots = []

    # -----------------------------
    # Create all employee nodes
    # -----------------------------
    for row in data:

        employee = dict(row)

        emp_id = normalize(
            employee.get("employee_number")
            or employee.get("EMPLOYEE NUMBER")
        )

        manager_id = normalize(
            employee.get("manager_id")
            or employee.get("MANAGER ID")
        )

        gender = str(
            employee.get("gender")
            or employee.get("GENDER")
            or ""
        ).lower()

        profile = (
            FEMALE_PROFILE
            if gender == "female"
            else MALE_PROFILE
        )

        frontend_employee = {

            "EMPLOYEE NUMBER": emp_id,
            "EMPLOYEE NAME":
                employee.get("employee_name")
                or employee.get("EMPLOYEE NAME"),

            "DESIGNATION":
                employee.get("designation")
                or employee.get("DESIGNATION"),

            "MANAGER ID": manager_id,

            "DATE OF JOINING":
                employee.get("date_of_joining")
                or employee.get("DATE OF JOINING"),

            "EMAIL ADDRESS":
                employee.get("email_address")
                or employee.get("EMAIL ADDRESS"),

            "LOCATION":
                employee.get("location")
                or employee.get("LOCATION"),

            "RESOURCE COUNTRY":
                employee.get("resource_country")
                or employee.get("RESOURCE COUNTRY"),

            "RESOURCE ONSITE OFFSHORE":
                employee.get("resource_onsite_offshore")
                or employee.get("RESOURCE ONSITE OFFSHORE"),

            "ONSITE OFFSHORE NEARSHORE":
                employee.get("onsite_offshore_nearshore")
                or employee.get("ONSITE OFFSHORE NEARSHORE"),

            "CLIENT LOCATION":
                employee.get("client_location")
                or employee.get("CLIENT LOCATION"),

            "EMP_WORK_LOCATION":
                employee.get("emp_work_location")
                or employee.get("EMP_WORK_LOCATION"),

            "FROM_DATE":
                employee.get("from_date")
                or employee.get("FROM_DATE"),

            "GENDER":
                employee.get("gender")
                or employee.get("GENDER"),

            "PROFILE": profile

        }

        nodes[emp_id] = {

            "id": emp_id,
            "name": frontend_employee["EMPLOYEE NAME"],
            "designation": frontend_employee["DESIGNATION"],
            "employee": frontend_employee,
            "children": []

        }

    # -----------------------------
    # Build Parent → Child links
    # -----------------------------
    for row in data:

        employee = dict(row)

        emp_id = normalize(
            employee.get("employee_number")
            or employee.get("EMPLOYEE NUMBER")
        )

        manager_id = normalize(
            employee.get("manager_id")
            or employee.get("MANAGER ID")
        )

        if manager_id is None:

            roots.append(nodes[emp_id])

        elif manager_id in nodes:

            nodes[manager_id]["children"].append(
                nodes[emp_id]
            )

        else:

            roots.append(nodes[emp_id])

    return roots


# ==================================================
# GET HIERARCHY
# ==================================================

def get_hierarchy():

    employees = get_all_employees()

    employees = [dict(emp) for emp in employees]

    return build_hierarchy(employees)


# ==================================================
# SEARCH EMPLOYEE
# ==================================================

def search_employee(search_text):

    hierarchy = get_hierarchy()

    results = []

    stack = hierarchy.copy()

    search = str(search_text).strip().lower()

    while stack:

        node = stack.pop()

        employee = node["employee"]

        emp_name = str(
            employee.get("EMPLOYEE NAME", "")
        ).lower()

        emp_number = str(
            employee.get("EMPLOYEE NUMBER", "")
        ).lower()

        if (
            search in emp_name
            or search in emp_number
        ):
            results.append(employee)

        stack.extend(node["children"])

    return results


# ==================================================
# ADD EMPLOYEE
# ==================================================

def add_employee(employee):

    gender = str(
        employee.get("gender", "")
    ).lower()

    employee["profile"] = (
        FEMALE_PROFILE
        if gender == "female"
        else MALE_PROFILE
    )

    insert_employee(employee)

    return get_hierarchy()


# ==================================================
# DELETE EMPLOYEE
# ==================================================

def delete_employee(employee_number):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM employees WHERE employee_number=?",

        (employee_number,)

    )

    conn.commit()

    conn.close()

    return get_hierarchy()


# ==================================================
# UPDATE EMPLOYEE
# ==================================================

def update_employee(employee_number, employee):

    def value(db_key, frontend_key):
        return employee.get(db_key) or employee.get(frontend_key)

    gender = str(value("gender", "GENDER")).lower()

    profile = (
        FEMALE_PROFILE
        if gender == "female"
        else MALE_PROFILE
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE employees
        SET
            employee_name=?,
            designation=?,
            manager_id=?,
            date_of_joining=?,
            email_address=?,
            location=?,
            resource_country=?,
            resource_onsite_offshore=?,
            onsite_offshore_nearshore=?,
            client_location=?,
            emp_work_location=?,
            from_date=?,
            gender=?,
            profile=?
        WHERE employee_number=?
        """,
        (
            value("employee_name", "EMPLOYEE NAME"),
            value("designation", "DESIGNATION"),
            normalize(value("manager_id", "MANAGER ID")),
            value("date_of_joining", "DATE OF JOINING"),
            value("email_address", "EMAIL ADDRESS"),
            value("location", "LOCATION"),
            value("resource_country", "RESOURCE COUNTRY"),
            value("resource_onsite_offshore", "RESOURCE ONSITE OFFSHORE"),
            value("onsite_offshore_nearshore", "ONSITE OFFSHORE NEARSHORE"),
            value("client_location", "CLIENT LOCATION"),
            value("emp_work_location", "EMP_WORK_LOCATION"),
            value("from_date", "FROM_DATE"),
            value("gender", "GENDER"),
            profile,
            employee_number
        )
    )

    conn.commit()
    conn.close()

    return get_hierarchy()
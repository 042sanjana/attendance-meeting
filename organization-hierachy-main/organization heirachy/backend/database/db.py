import sqlite3
import pandas as pd

DATABASE_NAME = "database/org.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE_NAME,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# CREATE TABLE
# ==========================================

def create_tables():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS employees(

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

    """)

    conn.commit()

    conn.close()


# ==========================================
# DELETE ALL EMPLOYEES
# ==========================================

def clear_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM employees"

    )

    conn.commit()

    conn.close()


# ==========================================
# NORMALIZE VALUES
# ==========================================

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


# ==========================================
# INSERT EMPLOYEE
# ==========================================

def insert_employee(employee):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        """

        INSERT INTO employees(

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

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?

        )

        """,

        (

            normalize(
                employee.get("employee_number")
                or employee.get("EMPLOYEE NUMBER")
            ),

            employee.get("employee_name")
            or employee.get("EMPLOYEE NAME"),

            employee.get("designation")
            or employee.get("DESIGNATION"),

            normalize(
                employee.get("manager_id")
                or employee.get("MANAGER ID")
            ),

            employee.get("date_of_joining")
            or employee.get("DATE OF JOINING"),

            employee.get("email_address")
            or employee.get("EMAIL ADDRESS"),

            employee.get("location")
            or employee.get("LOCATION"),

            employee.get("resource_country")
            or employee.get("RESOURCE COUNTRY"),

            employee.get("resource_onsite_offshore")
            or employee.get("RESOURCE ONSITE OFFSHORE"),

            employee.get("onsite_offshore_nearshore")
            or employee.get("ONSITE OFFSHORE NEARSHORE"),

            employee.get("client_location")
            or employee.get("CLIENT LOCATION"),

            employee.get("emp_work_location")
            or employee.get("EMP_WORK_LOCATION"),

            employee.get("from_date")
            or employee.get("FROM_DATE"),

            employee.get("gender")
            or employee.get("GENDER"),

            employee.get("profile")
            or employee.get("PROFILE")

        )

    )

    conn.commit()

    conn.close()


# ==========================================
# GET ALL EMPLOYEES
# ==========================================

def get_all_employees():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        """

        SELECT *

        FROM employees

        ORDER BY employee_number

        """

    )

    employees = cursor.fetchall()

    conn.close()

    return employees
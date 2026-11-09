"""Isolated ODC Tracker API. Uses separate tables; never mutates attendance tables."""

from datetime import datetime, date
from io import BytesIO
import json
import re

import pandas as pd

from fastapi import (
    APIRouter, Depends, UploadFile, File,
    HTTPException, Query, Body
)
from sqlalchemy import (
    Column, Integer, String, Date, DateTime,
    Text, UniqueConstraint, func
)
from sqlalchemy.orm import Session

from .database import Base, get_db


router = APIRouter(prefix="/api/odc", tags=["ODC Tracker"])


# =========================================================
# ODC DATABASE MODELS
# =========================================================

class ODCEmployee(Base):
    __tablename__ = "odc_employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(String(80), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=True)
    location = Column(String(100), nullable=True)
    project_name = Column(String(250), nullable=True)
    pm_name = Column(String(200), nullable=True)
    worked_from_odc = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)
    source_status = Column(String(80), nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class ODCEmployeeRemark(Base):
    """User-edited remarks are stored separately from Excel remarks."""

    __tablename__ = "odc_employee_remarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(String(80), unique=True, index=True, nullable=False)
    remarks = Column(Text, nullable=False, default='')
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class ODCLog(Base):
    __tablename__ = "odc_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(String(80), index=True, nullable=False)
    emp_name = Column(String(200), nullable=True)
    lob = Column(String(200), nullable=True)
    dm_name = Column(String(200), nullable=True)
    log_date = Column(Date, nullable=True, index=True)
    work_count = Column(String(80), nullable=True)
    upload_id = Column(Integer, nullable=True, index=True)
    raw_json = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            'emp_id',
            'log_date',
            'lob',
            'dm_name',
            name='uq_odc_log_identity'
        ),
    )


class ODCUpload(Base):
    __tablename__ = "odc_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    total_rows = Column(Integer, default=0)
    inserted_logs = Column(Integer, default=0)
    updated_employees = Column(Integer, default=0)
    unmatched_logs = Column(Integer, default=0)
    errors_json = Column(Text, nullable=True)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def norm_id(value):
    if pd.isna(value):
        return ''

    value = str(value).strip()

    if value.endswith('.0'):
        value = value[:-2]

    return re.sub(r'\s+', '', value).upper()


def norm_header(value):
    return re.sub(r'[^a-z0-9]+', '', str(value).lower())


def pick(row, *names):
    keys = {
        norm_header(key): key
        for key in row.index
    }

    for name in names:
        normalized = norm_header(name)

        if normalized in keys:
            return row[keys[normalized]]

    for key in row.index:
        normalized_key = norm_header(key)

        if any(
            norm_header(name) in normalized_key
            for name in names
        ):
            return row[key]

    return None


def clean(value):
    if value is None or pd.isna(value):
        return None

    value = str(value).strip()

    if value.lower() in ('nan', 'none', 'nat', ''):
        return None

    return value


def as_date(value):
    if value is None or pd.isna(value):
        return None

    try:
        return pd.to_datetime(value, errors='raise').date()
    except Exception:
        return None


# =========================================================
# EXCEL UPLOAD
# =========================================================

@router.post('/upload')
async def upload_odc(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(
        ('.xlsx', '.xlsm', '.xls')
    ):
        raise HTTPException(
            status_code=400,
            detail='Upload an Excel workbook (.xlsx or .xls).'
        )

    try:
        content = await file.read()

        book = pd.ExcelFile(BytesIO(content))

        raw_sheets = {
            str(sheet).strip().lower(): pd.read_excel(
                BytesIO(content),
                sheet_name=sheet,
                header=None,
                dtype=object
            )
            for sheet in book.sheet_names
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f'Could not read workbook: {exc}'
        )

    master_df = None
    logs_df = None

    # Find master and log tables, including when both
    # tables are placed vertically on the same worksheet.
    for raw_df in raw_sheets.values():

        header_rows = []

        for row_index, row in raw_df.iterrows():

            values = [
                norm_header(value)
                for value in row.tolist()
                if value is not None and not pd.isna(value)
            ]

            has_id = any(
                value in (
                    'empid',
                    'mphasisempid',
                    'employeeid'
                )
                for value in values
            )

            has_name = any(
                value in (
                    'empname',
                    'ftcname',
                    'employeename'
                )
                for value in values
            )

            is_log = (
                has_id
                and has_name
                and any('lob' in value for value in values)
                and any(
                    'date' in value or 'worked' in value
                    for value in values
                )
            )

            is_master = (
                has_id
                and any(
                    value in (
                        'ftcname',
                        'employeename',
                        'empname'
                    )
                    for value in values
                )
                and (
                    any('ftclocation' in value for value in values)
                    or any('projectname' in value for value in values)
                )
            )

            if is_log:
                header_rows.append(
                    (row_index, 'logs', row.tolist())
                )
            elif is_master:
                header_rows.append(
                    (row_index, 'master', row.tolist())
                )

        for index, (
            header_index,
            table_type,
            header
        ) in enumerate(header_rows):

            columns = []
            seen = {}

            for column_index, value in enumerate(header):

                label = clean(value) or f'Unnamed_{column_index}'

                seen[label] = seen.get(label, 0) + 1

                if seen[label] > 1:
                    label = f'{label}_{seen[label]}'

                columns.append(label)

            if index + 1 < len(header_rows):
                end_index = header_rows[index + 1][0]
            else:
                end_index = len(raw_df)

            block = raw_df.iloc[
                header_index + 1:end_index
            ].copy()

            block.columns = columns
            block = block.dropna(how='all')

            if table_type == 'master' and master_df is None:
                master_df = block

            if table_type == 'logs' and logs_df is None:
                logs_df = block

    if master_df is None:
        master_df = pd.DataFrame()

    if logs_df is None:
        raise HTTPException(
            status_code=400,
            detail=(
                'Could not identify the ODC log table. '
                'Expected headers similar to Emp ID, Emp Name, '
                'LOB, DM Name, and Date - Worked.'
            )
        )

    upload = ODCUpload(
        filename=file.filename,
        total_rows=int(len(logs_df))
    )

    db.add(upload)
    db.flush()

    errors = []
    inserted = 0
    updated = 0
    unmatched = 0

    # -----------------------------------------------------
    # UPDATE ODC EMPLOYEE MASTER DATA
    # -----------------------------------------------------

    master_ids = set()

    for _, row in master_df.iterrows():

        emp_id = norm_id(
            pick(
                row,
                'Mphasis EMP ID',
                'Emp ID',
                'Employee ID'
            )
        )

        if not emp_id:
            continue

        master_ids.add(emp_id)

        employee = db.query(ODCEmployee).filter_by(
            emp_id=emp_id
        ).first()

        if employee is None:
            employee = ODCEmployee(emp_id=emp_id)
            db.add(employee)

        employee.name = (
            clean(
                pick(
                    row,
                    'FTC Name',
                    'Emp Name',
                    'Employee Name'
                )
            ) or employee.name
        )

        employee.location = (
            clean(
                pick(row, 'FTC Location', 'Location')
            ) or employee.location
        )

        employee.project_name = (
            clean(
                pick(
                    row,
                    'JPMC Project Name where FTC Tagged',
                    'JPMC Project Name',
                    'Project Name'
                )
            ) or employee.project_name
        )

        employee.pm_name = (
            clean(
                pick(row, 'Mphasis India PM', 'PM Name')
            ) or employee.pm_name
        )

        worked = clean(pick(row, 'Worked from ODC'))

        if worked and worked.lower() not in (
            '#n/a',
            'n/a',
            'na'
        ):
            try:
                employee.worked_from_odc = int(float(worked))
            except ValueError:
                pass

        employee.source_status = 'Present in roster'

        updated += 1

    db.flush()

    # -----------------------------------------------------
    # UPDATE ODC LOGS
    # -----------------------------------------------------

    for _, row in logs_df.iterrows():

        emp_id = norm_id(
            pick(
                row,
                'Emp ID',
                'Mphasis EMP ID',
                'Employee ID'
            )
        )

        if not emp_id:
            errors.append(
                'Row with missing employee ID skipped'
            )
            continue

        log_date = as_date(
            pick(
                row,
                'Date - Worked',
                'Date',
                'Work Date',
                'Log Date'
            )
        )

        if not log_date:
            errors.append(
                f'Employee {emp_id}: missing/invalid date; raw row skipped'
            )
            continue

        emp_name = clean(
            pick(
                row,
                'Emp Name',
                'FTC Name',
                'Employee Name'
            )
        )

        lob = clean(pick(row, 'LOB'))
        dm = clean(pick(row, 'DM Name'))

        count = clean(
            pick(row, 'Work Count', 'Count', 'Hours')
        )

        raw = {
            str(key): (
                None if pd.isna(value) else str(value)
            )
            for key, value in row.to_dict().items()
        }

        existing = db.query(ODCLog).filter_by(
            emp_id=emp_id,
            log_date=log_date,
            lob=lob,
            dm_name=dm
        ).first()

        if existing:
            existing.emp_name = (
                emp_name or existing.emp_name
            )

            existing.work_count = (
                count or existing.work_count
            )

            existing.raw_json = json.dumps(raw)
            existing.upload_id = upload.id

        else:
            db.add(
                ODCLog(
                    emp_id=emp_id,
                    emp_name=emp_name,
                    lob=lob,
                    dm_name=dm,
                    log_date=log_date,
                    work_count=count,
                    upload_id=upload.id,
                    raw_json=json.dumps(raw)
                )
            )

            inserted += 1

        if (
            master_ids
            and emp_id not in master_ids
            and not db.query(ODCEmployee).filter_by(
                emp_id=emp_id
            ).first()
        ):
            unmatched += 1

    upload.inserted_logs = inserted
    upload.updated_employees = updated
    upload.unmatched_logs = unmatched
    upload.errors_json = json.dumps(errors)

    db.commit()

    return {
        'message': 'ODC workbook processed successfully',
        'upload_id': upload.id,
        'filename': file.filename,
        'log_rows': len(logs_df),
        'inserted_logs': inserted,
        'roster_rows_upserted': updated,
        'unmatched_log_ids': unmatched,
        'errors': errors[:100]
    }


# =========================================================
# ODC SUMMARY
# =========================================================

@router.get('/summary')
def summary(
    search: str = '',
    location: str = '',
    project: str = '',
    db: Session = Depends(get_db)
):

    employees = db.query(ODCEmployee).all()

    log_counts = {}

    results = db.query(
        ODCLog.emp_id,
        func.count(func.distinct(ODCLog.log_date))
    ).group_by(ODCLog.emp_id).all()

    for emp_id, count in results:
        log_counts[emp_id] = count

    manual_remarks = {
        remark.emp_id: remark.remarks
        for remark in db.query(ODCEmployeeRemark).all()
    }

    rows = []

    for employee in employees:

        if search and search.lower() not in (
            employee.emp_id + ' ' + (employee.name or '')
        ).lower():
            continue

        if location and location.lower() not in (
            employee.location or ''
        ).lower():
            continue

        if project and project.lower() not in (
            employee.project_name or ''
        ).lower():
            continue

        rows.append({
            'emp_id': employee.emp_id,
            'name': employee.name,
            'location': employee.location,
            'project_name': employee.project_name,
            'pm_name': employee.pm_name,
            'worked_from_odc': employee.worked_from_odc,
            'distinct_log_days': log_counts.get(
                employee.emp_id,
                0
            ),
            'remarks': (
                manual_remarks[employee.emp_id]
                if employee.emp_id in manual_remarks
                else employee.remarks
            ),
            'source_status': employee.source_status
        })

    return {
        'total_employees': len(employees),
        'total_log_rows': db.query(ODCLog).count(),
        'matched_employees': sum(
            1 for row in rows
            if row['distinct_log_days'] > 0
        ),
        'employees': rows
    }


# =========================================================
# ODC ANALYTICS
# =========================================================

@router.get('/analytics')
def odc_analytics(
    year: int = Query(None, ge=2000, le=2100),
    month: int = Query(None, ge=1, le=12),
    emp_id: str = Query(''),
    search: str = Query(''),
    location: str = Query(''),
    project: str = Query(''),
    db: Session = Depends(get_db)
):

    normalized_emp_id = norm_id(emp_id) if emp_id else ''

    roster = db.query(ODCEmployee).order_by(
        ODCEmployee.emp_id
    ).all()

    filtered_roster = []

    search_value = (search or '').strip().lower()
    location_value = (location or '').strip().lower()
    project_value = (project or '').strip().lower()

    for employee in roster:

        searchable = (
            f"{employee.emp_id} {employee.name or ''}"
        ).lower()

        if search_value and search_value not in searchable:
            continue

        if location_value and location_value not in (
            employee.location or ''
        ).lower():
            continue

        if project_value and project_value not in (
            employee.project_name or ''
        ).lower():
            continue

        if (
            normalized_emp_id
            and employee.emp_id != normalized_emp_id
        ):
            continue

        filtered_roster.append(employee)

    # Available years are taken from ODC logs only.
    year_values = [
        int(value)
        for (value,) in db.query(
            func.strftime('%Y', ODCLog.log_date)
        ).filter(
            ODCLog.log_date.isnot(None)
        ).distinct().all()
        if value
    ]

    years = sorted(set(year_values), reverse=True)

    log_query = db.query(
        ODCLog.emp_id,
        ODCLog.log_date,
        ODCLog.emp_name
    ).filter(
        ODCLog.log_date.isnot(None)
    )

    if year is not None:
        log_query = log_query.filter(
            func.strftime('%Y', ODCLog.log_date) == str(year)
        )

    if month is not None:
        log_query = log_query.filter(
            func.strftime('%m', ODCLog.log_date)
            == f'{month:02d}'
        )

    if normalized_emp_id:
        log_query = log_query.filter(
            ODCLog.emp_id == normalized_emp_id
        )

    roster_filter_active = bool(
        search_value or location_value or project_value
    )

    if roster_filter_active:

        allowed_ids = {
            employee.emp_id
            for employee in filtered_roster
        }

        if normalized_emp_id:
            allowed_ids = (
                {normalized_emp_id}
                if normalized_emp_id in allowed_ids
                else set()
            )

        if not allowed_ids:
            log_rows = []
        else:
            log_rows = [
                row for row in log_query.all()
                if row[0] in allowed_ids
            ]

    else:
        log_rows = log_query.all()

    employee_by_id = {
        employee.emp_id: employee
        for employee in filtered_roster
    }

    name_by_id = {}
    date_sets = {}

    monthly_sets = {
        month_number: set()
        for month_number in range(1, 13)
    }

    for log_emp_id, log_date, log_name in log_rows:

        if not log_emp_id or not log_date:
            continue

        name_by_id.setdefault(log_emp_id, log_name)

        date_sets.setdefault(
            log_emp_id,
            set()
        ).add(log_date)

        # Count one working day for an employee on a date,
        # even if multiple LOB/DM rows exist for that date.
        monthly_sets[log_date.month].add(
            (log_emp_id, log_date)
        )

    # Include roster employees even when they have zero days.
    scope_ids = set(employee_by_id)

    if not roster_filter_active:
        scope_ids.update(date_sets)

    if normalized_emp_id:
        scope_ids = (
            {normalized_emp_id}
            if (
                normalized_emp_id in scope_ids
                or normalized_emp_id in date_sets
            )
            else set()
        )

    employee_stats = []

    for current_id in scope_ids:

        employee = employee_by_id.get(current_id)

        days = len(
            date_sets.get(current_id, set())
        )

        employee_stats.append({
            'emp_id': current_id,
            'name': (
                (employee.name if employee else None)
                or name_by_id.get(current_id)
                or current_id
            ),
            'location': (
                employee.location if employee else None
            ),
            'project_name': (
                employee.project_name if employee else None
            ),
            'working_days': days
        })

    employee_stats.sort(
        key=lambda item: (
            -item['working_days'],
            (item['name'] or '').lower(),
            item['emp_id']
        )
    )

    total_working_days = sum(
        item['working_days']
        for item in employee_stats
    )

    total_employees = len(employee_stats)

    average_working_days = (
        round(
            total_working_days / total_employees,
            1
        )
        if total_employees
        else 0
    )

    highest_employee = (
        employee_stats[0]
        if (
            employee_stats
            and employee_stats[0]['working_days'] > 0
        )
        else None
    )

    month_names = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December'
    ]

    monthly = []

    for month_number, month_name in enumerate(
        month_names,
        start=1
    ):

        count = (
            0
            if month is not None and month != month_number
            else len(monthly_sets[month_number])
        )

        if normalized_emp_id:
            count = sum(
                1
                for employee_id, _ in monthly_sets[month_number]
                if employee_id == normalized_emp_id
            )

            if month is not None and month != month_number:
                count = 0

        if roster_filter_active:

            allowed = {
                employee.emp_id
                for employee in filtered_roster
            }

            count = sum(
                1
                for employee_id, _ in monthly_sets[month_number]
                if employee_id in allowed
            )

            if normalized_emp_id:
                count = sum(
                    1
                    for employee_id, _ in monthly_sets[month_number]
                    if (
                        employee_id == normalized_emp_id
                        and employee_id in allowed
                    )
                )

            if month is not None and month != month_number:
                count = 0

        monthly.append({
            'month_number': month_number,
            'month': month_name,
            'working_days': count
        })

    return {
        'filters': {
            'year': year,
            'month': month,
            'emp_id': normalized_emp_id or None
        },
        'years': years,
        'months': [
            {
                'value': index,
                'label': name
            }
            for index, name in enumerate(
                month_names,
                start=1
            )
        ],
        'cards': {
            'total_odc_working_days': total_working_days,
            'total_employees': total_employees,
            'average_working_days': average_working_days,
            'highest_employee': highest_employee
        },
        'monthly': monthly,
        'employees': employee_stats
    }


# =========================================================
# RESET ODC DATA ONLY
# =========================================================

@router.delete('/reset')
def reset_odc_data(
    db: Session = Depends(get_db)
):

    try:
        deleted_remarks = db.query(
            ODCEmployeeRemark
        ).delete(synchronize_session=False)

        deleted_logs = db.query(
            ODCLog
        ).delete(synchronize_session=False)

        deleted_uploads = db.query(
            ODCUpload
        ).delete(synchronize_session=False)

        deleted_employees = db.query(
            ODCEmployee
        ).delete(synchronize_session=False)

        db.commit()

        return {
            'message': (
                'ODC data reset successfully. '
                'Attendance data was not changed.'
            ),
            'deleted_odc_employees': deleted_employees,
            'deleted_odc_logs': deleted_logs,
            'deleted_odc_uploads': deleted_uploads,
            'deleted_odc_remarks': deleted_remarks
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f'Could not reset ODC data: {exc}'
        )


# =========================================================
# UPDATE EMPLOYEE REMARKS
# =========================================================

@router.put('/employees/{emp_id}/remarks')
def update_employee_remarks(
    emp_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):

    normalized_id = norm_id(emp_id)

    if not normalized_id:
        raise HTTPException(
            status_code=400,
            detail='A valid employee ID is required.'
        )

    if (
        not isinstance(payload, dict)
        or 'remarks' not in payload
    ):
        raise HTTPException(
            status_code=422,
            detail='Request body must include a remarks field.'
        )

    value = payload.get('remarks')

    if value is None:
        value = ''

    if not isinstance(value, str):
        raise HTTPException(
            status_code=422,
            detail='Remarks must be text.'
        )

    value = value.strip()

    if len(value) > 2000:
        raise HTTPException(
            status_code=422,
            detail='Remarks must be 2000 characters or fewer.'
        )

    employee = db.query(ODCEmployee).filter_by(
        emp_id=normalized_id
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail='Employee not found in the ODC roster.'
        )

    manual = db.query(ODCEmployeeRemark).filter_by(
        emp_id=normalized_id
    ).first()

    if manual is None:
        manual = ODCEmployeeRemark(
            emp_id=normalized_id,
            remarks=value
        )

        db.add(manual)

    else:
        manual.remarks = value
        manual.updated_at = datetime.utcnow()

    db.commit()

    return {
        'message': 'Remarks saved successfully.',
        'emp_id': employee.emp_id,
        'remarks': manual.remarks
    }


# =========================================================
# ODC LOGS
# =========================================================

@router.get('/logs')
def logs(
    emp_id: str = '',
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):

    query = db.query(ODCLog)

    if emp_id:
        query = query.filter(
            ODCLog.emp_id == norm_id(emp_id)
        )

    if start_date:
        query = query.filter(
            ODCLog.log_date >= start_date
        )

    if end_date:
        query = query.filter(
            ODCLog.log_date <= end_date
        )

    records = query.order_by(
        ODCLog.log_date.desc()
    ).limit(5000).all()

    return [
        {
            'id': record.id,
            'emp_id': record.emp_id,
            'emp_name': record.emp_name,
            'lob': record.lob,
            'dm_name': record.dm_name,
            'log_date': (
                record.log_date.isoformat()
                if record.log_date
                else None
            ),
            'work_count': record.work_count,
            'raw': (
                json.loads(record.raw_json)
                if record.raw_json
                else {}
            )
        }
        for record in records
    ]


# =========================================================
# ODC UPLOAD HISTORY
# =========================================================

@router.get('/uploads')
def uploads(
    db: Session = Depends(get_db)
):

    records = db.query(ODCUpload).order_by(
        ODCUpload.id.desc()
    ).limit(50).all()

    return [
        {
            'id': record.id,
            'filename': record.filename,
            'uploaded_at': (
                record.uploaded_at.isoformat()
                if record.uploaded_at
                else None
            ),
            'total_rows': record.total_rows,
            'inserted_logs': record.inserted_logs,
            'updated_employees': record.updated_employees,
            'unmatched_logs': record.unmatched_logs,
            'errors': json.loads(
                record.errors_json or '[]'
            )
        }
        for record in records
    ]
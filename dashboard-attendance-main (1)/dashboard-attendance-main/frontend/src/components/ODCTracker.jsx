import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react'


import {
  Search,
  UploadCloud,
  Users,
  CalendarDays,
  AlertTriangle,
  RefreshCw,
  FileSpreadsheet,
  Pencil,
  Save,
  X,
  LoaderCircle,
  BarChart3,
  Trophy,
  TrendingUp,
  Database,
  Trash2,
  Filter,
} from 'lucide-react'

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from 'recharts'

import api from '../api.js'
import './ODCTracker.css'


const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]

const EMPTY_SUMMARY = {
  employees: [],
  total_employees: 0,
  total_log_rows: 0,
  matched_employees: 0,
}

const EMPTY_ANALYTICS = {
  years: [],
  cards: {
    total_odc_working_days: 0,
    total_employees: 0,
    average_working_days: 0,
    highest_employee: null,
  },
  monthly: MONTHS.map((item) => ({
    month_number: item.value,
    month: item.label,
    working_days: 0,
  })),
  employees: [],
}


export default function ODCTracker() {
  const [summary, setSummary] = useState(EMPTY_SUMMARY)
  const [analytics, setAnalytics] = useState(EMPTY_ANALYTICS)
  const [logs, setLogs] = useState([])
  const [uploads, setUploads] = useState([])

  // Existing roster filters.
  const [search, setSearch] = useState('')
  const [location, setLocation] = useState('')
  const [project, setProject] = useState('')

  // Analytics filters.
  const [selectedYear, setSelectedYear] = useState('')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [selectedEmployee, setSelectedEmployee] = useState('')

  // Existing log filters.
  const [logEmployee, setLogEmployee] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  const [file, setFile] = useState(null)
  const fileInputRef = useRef(null)

  const [busy, setBusy] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [resetting, setResetting] = useState(false)

  const [showResetConfirm, setShowResetConfirm] = useState(false)

  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const [tab, setTab] = useState('analytics')

  const [editingEmp, setEditingEmp] = useState('')
  const [editRemark, setEditRemark] = useState('')
  const [savingRemark, setSavingRemark] = useState(false)


  // =====================================================
  // LOAD ALL ODC DATA
  // =====================================================

  const load = useCallback(async (options = {}) => {
    const clearFilters = Boolean(options.clearFilters)

    const rosterParams = clearFilters
      ? {}
      : {
          search,
          location,
          project,
        }

    const analyticsParams = clearFilters
      ? {}
      : {
          year: selectedYear || undefined,
          month: selectedMonth || undefined,
          emp_id: selectedEmployee || undefined,
          search: search || undefined,
          location: location || undefined,
          project: project || undefined,
        }

    const logParams = clearFilters
      ? {}
      : {
          emp_id: logEmployee || undefined,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }

    setRefreshing(true)

    try {
      const [
        summaryRes,
        logsRes,
        uploadsRes,
        analyticsRes,
      ] = await Promise.all([
        api.get('/odc/summary', {
          params: rosterParams,
        }),

        api.get('/odc/logs', {
          params: logParams,
        }),

        api.get('/odc/uploads'),

        api.get('/odc/analytics', {
          params: analyticsParams,
        }),
      ])

      setSummary(summaryRes.data)
      setLogs(logsRes.data)
      setUploads(uploadsRes.data)
      setAnalytics(analyticsRes.data)

      setError('')
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Could not load ODC analytics. Check that the FastAPI backend is running.'
      )
    } finally {
      setRefreshing(false)
    }
  }, [
    search,
    location,
    project,
    selectedYear,
    selectedMonth,
    selectedEmployee,
    logEmployee,
    startDate,
    endDate,
  ])


  useEffect(() => {
    load()
  }, [load])


  // =====================================================
  // FILTER OPTIONS
  // =====================================================

  const locations = useMemo(
    () => [
      ...new Set(
        (summary.employees || [])
          .map((item) => item.location)
          .filter(Boolean)
      ),
    ].sort(),
    [summary.employees]
  )

  const projects = useMemo(
    () => [
      ...new Set(
        (summary.employees || [])
          .map((item) => item.project_name)
          .filter(Boolean)
      ),
    ].sort(),
    [summary.employees]
  )


  // =====================================================
  // EMPLOYEE COMPARISON CHART DATA
  // =====================================================

  const employeeChartData = useMemo(
    () => (analytics.employees || [])
      .filter((employee) => employee.working_days > 0)
      .slice(0, 12)
      .map((employee) => ({
        ...employee,

        label:
          employee.name &&
          employee.name !== employee.emp_id
            ? `${employee.name} (${employee.emp_id})`
            : employee.emp_id,
      })),
    [analytics.employees]
  )

  const highestEmployee = analytics.cards?.highest_employee

  const cards = analytics.cards || EMPTY_ANALYTICS.cards


  // =====================================================
  // REMARKS EDITING
  // =====================================================

  function startEditingRemark(employee) {
    setEditingEmp(employee.emp_id)
    setEditRemark(employee.remarks || '')
    setError('')
    setMessage('')
  }

  function cancelEditingRemark() {
    setEditingEmp('')
    setEditRemark('')
  }

  async function saveRemark(empId) {
    setSavingRemark(true)
    setError('')
    setMessage('')

    try {
      await api.put(
        `/odc/employees/${encodeURIComponent(empId)}/remarks`,
        {
          remarks: editRemark,
        }
      )

      setMessage(`Remarks saved for employee ${empId}.`)

      setEditingEmp('')
      setEditRemark('')

      await load()
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Could not save remarks. Please try again.'
      )
    } finally {
      setSavingRemark(false)
    }
  }


  // =====================================================
  // EXCEL UPLOAD
  // =====================================================

  async function upload() {
    if (!file) {
      setError('Choose the ODC Excel workbook first.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setBusy(true)
    setError('')
    setMessage('')

    try {
      const response = await api.post(
        '/odc/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setMessage(
        `Upload complete: ${response.data.inserted_logs} new log rows, ` +
        `${response.data.roster_rows_upserted} roster rows processed, ` +
        `${response.data.unmatched_log_ids} unmatched IDs. Analytics refreshed.`
      )

      setFile(null)

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      await load()
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Upload failed. Check workbook columns and try again.'
      )
    } finally {
      setBusy(false)
    }
  }


  // =====================================================
  // RESET ODC DATA ONLY
  // =====================================================

  async function resetODCData() {
    setResetting(true)
    setError('')
    setMessage('')

    try {
      const response = await api.delete('/odc/reset')

      setShowResetConfirm(false)

      setSearch('')
      setLocation('')
      setProject('')

      setSelectedYear('')
      setSelectedMonth('')
      setSelectedEmployee('')

      setLogEmployee('')
      setStartDate('')
      setEndDate('')

      setEditingEmp('')
      setEditRemark('')

      setFile(null)

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      setMessage(
        response.data.message ||
        'ODC data reset successfully. Attendance data was not changed.'
      )

      // This refresh reads only the ODC tables.
      await load({
        clearFilters: true,
      })
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        'Could not reset ODC data. No attendance reset was requested.'
      )
    } finally {
      setResetting(false)
    }
  }


  function clearLogFilters() {
    setLogEmployee('')
    setStartDate('')
    setEndDate('')
  }


  // =====================================================
  // PAGE UI
  // =====================================================

  return (
    <div className="odc-page">

      {/* PAGE HEADER */}

      <div className="odc-heading">
        <div>
          <div className="odc-eyebrow">
            HR PORTAL / OPERATIONS
          </div>

          <h1>ODC Tracker Analytics</h1>

          <p>
            Monitor monthly ODC working days, compare employee
            participation and reconcile uploaded ODC records.
          </p>
        </div>

        <div className="odc-heading-actions">

          <button
            className="odc-refresh"
            type="button"
            onClick={() => load()}
            disabled={refreshing || resetting}
          >
            <RefreshCw
              size={16}
              className={refreshing ? 'odc-spin' : ''}
            />

            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>

          <button
            className="odc-reset-button"
            type="button"
            onClick={() => setShowResetConfirm(true)}
            disabled={resetting || busy}
          >
            <Trash2 size={16} />
            Reset ODC Data
          </button>

        </div>
      </div>


      {/* SUCCESS AND ERROR MESSAGES */}

      {error && (
        <div className="odc-alert error">
          <AlertTriangle size={17} />
          {error}
        </div>
      )}

      {message && (
        <div className="odc-alert success">
          {message}
        </div>
      )}


      {/* EXCEL UPLOAD */}

      <div className="odc-upload-panel">

        <div className="odc-upload-icon">
          <FileSpreadsheet size={22} />
        </div>

        <div className="odc-upload-copy">
          <strong>Import ODC workbook</strong>

          <span>
            Upload the workbook containing the ODC logs and employee
            roster. Existing ODC records are reconciled; attendance
            records remain untouched.
          </span>
        </div>

        <input
          ref={fileInputRef}
          id="odc-file-input"
          type="file"
          accept=".xlsx,.xls,.xlsm"
          onChange={(event) => {
            setFile(event.target.files?.[0] || null)
          }}
        />

        <button
          type="button"
          disabled={busy || !file}
          onClick={upload}
        >
          <UploadCloud size={16} />
          {busy ? 'Processing…' : 'Upload & Reconcile'}
        </button>

      </div>


      {/* ANALYTICS FILTERS */}

      <section className="odc-filter-panel">

        <div className="odc-filter-title">
          <Filter size={16} />
          <strong>Analytics filters</strong>

          <span>
            Filters update the ODC cards, graphs and statistics.
          </span>
        </div>

        <div className="odc-filters odc-analytics-filters">

          <label>
            <span>Year</span>

            <select
              value={selectedYear}
              onChange={(event) => {
                setSelectedYear(event.target.value)
              }}
            >
              <option value="">All years</option>

              {(analytics.years || []).map((year) => (
                <option key={year} value={String(year)}>
                  {year}
                </option>
              ))}
            </select>
          </label>


          <label>
            <span>Month</span>

            <select
              value={selectedMonth}
              onChange={(event) => {
                setSelectedMonth(event.target.value)
              }}
            >
              <option value="">All months</option>

              {MONTHS.map((item) => (
                <option
                  key={item.value}
                  value={String(item.value)}
                >
                  {item.label}
                </option>
              ))}
            </select>
          </label>


          <label>
            <span>Employee</span>

            <select
              value={selectedEmployee}
              onChange={(event) => {
                setSelectedEmployee(event.target.value)
              }}
            >
              <option value="">All employees</option>

              {(summary.employees || []).map((employee) => (
                <option
                  key={employee.emp_id}
                  value={employee.emp_id}
                >
                  {employee.emp_id} — {employee.name || 'Unknown'}
                </option>
              ))}
            </select>
          </label>


          <label className="odc-filter-search">
            <span>Search roster</span>

            <div className="odc-search">
              <Search size={16} />

              <input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value)
                }}
                placeholder="Employee name or ID…"
              />
            </div>
          </label>


          <label>
            <span>Location</span>

            <select
              value={location}
              onChange={(event) => {
                setLocation(event.target.value)
              }}
            >
              <option value="">All locations</option>

              {locations.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>


          <label>
            <span>Project</span>

            <select
              value={project}
              onChange={(event) => {
                setProject(event.target.value)
              }}
            >
              <option value="">All projects</option>

              {projects.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

        </div>
      </section>


      {/* KPI CARDS */}

      <div className="odc-metrics odc-analytics-metrics">

        <div className="odc-metric">
          <span>
            <CalendarDays size={17} />
            Total ODC working days
          </span>

          <strong>
            {cards.total_odc_working_days ?? 0}
          </strong>

          <small>
            Unique employee and date combinations
          </small>
        </div>


        <div className="odc-metric">
          <span>
            <Users size={17} />
            Total employees
          </span>

          <strong>
            {cards.total_employees ?? 0}
          </strong>

          <small>
            Employees in the selected scope
          </small>
        </div>


        <div className="odc-metric">
          <span>
            <TrendingUp size={17} />
            Average working days
          </span>

          <strong>
            {cards.average_working_days ?? 0}
          </strong>

          <small>
            Working days per employee
          </small>
        </div>


        <div className="odc-metric odc-top-metric">
          <span>
            <Trophy size={17} />
            Highest ODC employee
          </span>

          <strong>
            {highestEmployee?.working_days
              ? highestEmployee.working_days
              : '—'}
          </strong>

          <small>
            {highestEmployee
              ? `${highestEmployee.name} · ${highestEmployee.emp_id}`
              : 'No ODC days in this filter'}
          </small>
        </div>

      </div>


      {/* NAVIGATION TABS */}

      <div className="odc-tabs">

        <button
          className={tab === 'analytics' ? 'active' : ''}
          onClick={() => setTab('analytics')}
        >
          Analytics overview
        </button>

        <button
          className={tab === 'roster' ? 'active' : ''}
          onClick={() => setTab('roster')}
        >
          Employee reconciliation
        </button>

        <button
          className={tab === 'logs' ? 'active' : ''}
          onClick={() => setTab('logs')}
        >
          ODC logs
        </button>

        <button
          className={tab === 'uploads' ? 'active' : ''}
          onClick={() => setTab('uploads')}
        >
          Upload history
        </button>

      </div>


      {/* =================================================
          ANALYTICS OVERVIEW
      ================================================= */}

      {tab === 'analytics' && (
        <>

          <div className="odc-analytics-grid">

            {/* MONTHLY GRAPH */}

            <section className="odc-chart-panel odc-monthly-panel">

              <div className="odc-chart-header">
                <div>
                  <div className="odc-eyebrow">
                    MONTHLY TREND
                  </div>

                  <h3>
                    ODC working days · January–December
                  </h3>

                  <p>
                    Each employee is counted once per calendar date,
                    even if multiple ODC log rows exist.
                  </p>
                </div>

                <span className="odc-chart-chip">
                  {selectedYear || 'All years'}
                </span>
              </div>

              <div className="odc-chart-wrap odc-monthly-chart">

                <ResponsiveContainer width="100%" height="100%">

                  <BarChart
                    data={
                      analytics.monthly ||
                      EMPTY_ANALYTICS.monthly
                    }
                    margin={{
                      top: 12,
                      right: 18,
                      left: -12,
                      bottom: 4,
                    }}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#edf1f7"
                    />

                    <XAxis
                      dataKey="month"
                      tick={{
                        fontSize: 11,
                        fill: '#6a7287',
                      }}
                      interval={0}
                    />

                    <YAxis
                      allowDecimals={false}
                      tick={{
                        fontSize: 11,
                        fill: '#6a7287',
                      }}
                    />

                    <Tooltip
                      formatter={(value) => [
                        `${value} employee-days`,
                        'ODC working days',
                      ]}
                      contentStyle={{
                        borderRadius: 10,
                        border: '1px solid #e5e7ef',
                        fontSize: 12,
                      }}
                    />

                    <Bar
                      dataKey="working_days"
                      name="ODC working days"
                      fill="#5145cd"
                      radius={[7, 7, 0, 0]}
                      maxBarSize={42}
                    />

                  </BarChart>

                </ResponsiveContainer>

              </div>
            </section>


            {/* EMPLOYEE COMPARISON GRAPH */}

            <section className="odc-chart-panel odc-employee-panel">

              <div className="odc-chart-header">
                <div>
                  <div className="odc-eyebrow">
                    EMPLOYEE COMPARISON
                  </div>

                  <h3>
                    Top employees by ODC days
                  </h3>

                  <p>
                    Top 12 employees in the selected filter.
                  </p>
                </div>

                <BarChart3
                  size={20}
                  className="odc-panel-icon"
                />
              </div>

              {employeeChartData.length ? (

                <div className="odc-employee-chart">

                  <ResponsiveContainer
                    width="100%"
                    height={Math.max(
                      260,
                      employeeChartData.length * 38
                    )}
                  >

                    <BarChart
                      data={employeeChartData}
                      layout="vertical"
                      margin={{
                        top: 5,
                        right: 18,
                        left: 8,
                        bottom: 5,
                      }}
                    >

                      <CartesianGrid
                        strokeDasharray="3 3"
                        horizontal={false}
                        stroke="#edf1f7"
                      />

                      <XAxis
                        type="number"
                        allowDecimals={false}
                        tick={{
                          fontSize: 11,
                          fill: '#6a7287',
                        }}
                      />

                      <YAxis
                        type="category"
                        dataKey="label"
                        width={135}
                        tick={{
                          fontSize: 10,
                          fill: '#596176',
                        }}
                      />

                      <Tooltip
                        formatter={(value) => [
                          `${value} days`,
                          'ODC working days',
                        ]}
                        contentStyle={{
                          borderRadius: 10,
                          border: '1px solid #e5e7ef',
                          fontSize: 12,
                        }}
                      />

                      <Bar
                        dataKey="working_days"
                        name="ODC working days"
                        radius={[0, 7, 7, 0]}
                        maxBarSize={22}
                      >
                        {employeeChartData.map(
                          (employee, index) => (
                            <Cell
                              key={employee.emp_id}
                              fill={
                                index === 0
                                  ? '#5145cd'
                                  : '#8b82e8'
                              }
                            />
                          )
                        )}
                      </Bar>

                    </BarChart>

                  </ResponsiveContainer>

                </div>

              ) : (

                <div className="odc-chart-empty">
                  No employee working-day data for the selected filters.
                </div>

              )}

            </section>

          </div>


          {/* EMPLOYEE STATISTICS TABLE */}

          <section className="odc-statistics-panel">

            <div className="odc-chart-header">
              <div>
                <div className="odc-eyebrow">
                  EMPLOYEE STATISTICS
                </div>

                <h3>
                  Employee-wise ODC working days
                </h3>

                <p>
                  Sorted from highest to lowest distinct working days.
                </p>
              </div>

              <span className="odc-record-count">
                {analytics.employees?.length || 0} employees
              </span>
            </div>

            <div className="odc-table-wrap odc-stats-table-wrap">

              <table className="odc-table odc-stats-table">

                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Employee ID</th>
                    <th>Employee name</th>
                    <th>Location</th>
                    <th>Project</th>
                    <th>ODC working days</th>
                    <th>Share of total</th>
                  </tr>
                </thead>

                <tbody>

                  {(analytics.employees || []).map(
                    (employee, index) => {

                      const share = cards.total_odc_working_days
                        ? (
                            employee.working_days /
                            cards.total_odc_working_days
                          ) * 100
                        : 0

                      return (
                        <tr key={employee.emp_id}>

                          <td>
                            <span
                              className={`odc-rank ${
                                index === 0 &&
                                employee.working_days > 0
                                  ? 'first'
                                  : ''
                              }`}
                            >
                              {index + 1}
                            </span>
                          </td>

                          <td className="odc-id">
                            {employee.emp_id}
                          </td>

                          <td>
                            {employee.name || '—'}
                          </td>

                          <td>
                            {employee.location || '—'}
                          </td>

                          <td>
                            {employee.project_name || '—'}
                          </td>

                          <td>
                            <span
                              className={
                                employee.working_days
                                  ? 'odc-count good'
                                  : 'odc-count'
                              }
                            >
                              {employee.working_days}
                            </span>
                          </td>

                          <td>
                            {share.toFixed(1)}%
                          </td>

                        </tr>
                      )
                    }
                  )}

                  {!analytics.employees?.length && (
                    <tr>
                      <td colSpan="7" className="odc-empty">
                        No employee statistics match the selected filters.
                      </td>
                    </tr>
                  )}

                </tbody>
              </table>
            </div>

          </section>

        </>
      )}


      {/* =================================================
          EMPLOYEE RECONCILIATION
      ================================================= */}

      {tab === 'roster' && (

        <div className="odc-table-wrap">

          <table className="odc-table">

            <thead>
              <tr>
                <th>Mphasis EMP ID</th>
                <th>FTC Name</th>
                <th>FTC Location</th>
                <th>JPMC Project</th>
                <th>Mphasis India PM</th>
                <th>Worked from ODC</th>
                <th>Distinct log days</th>
                <th>Remarks / Comments</th>
              </tr>
            </thead>

            <tbody>

              {(summary.employees || []).map((employee) => (

                <tr key={employee.emp_id}>

                  <td className="odc-id">
                    {employee.emp_id}
                  </td>

                  <td>
                    {employee.name || '—'}
                  </td>

                  <td>
                    {employee.location || '—'}
                  </td>

                  <td>
                    {employee.project_name || '—'}
                  </td>

                  <td>
                    {employee.pm_name || '—'}
                  </td>

                  <td>
                    {employee.worked_from_odc ?? '—'}
                  </td>

                  <td>
                    <span
                      className={
                        employee.distinct_log_days
                          ? 'odc-count good'
                          : 'odc-count'
                      }
                    >
                      {employee.distinct_log_days}
                    </span>
                  </td>

                  <td className="odc-remarks-cell">

                    {editingEmp === employee.emp_id ? (

                      <div className="odc-remark-editor">

                        <textarea
                          aria-label={`Remarks for ${employee.emp_id}`}
                          maxLength={2000}
                          value={editRemark}
                          onChange={(event) => {
                            setEditRemark(event.target.value)
                          }}
                          placeholder="Enter comments or remarks…"
                          rows={3}
                        />

                        <div className="odc-remark-actions">

                          <button
                            type="button"
                            className="odc-save-remark"
                            onClick={() => saveRemark(employee.emp_id)}
                            disabled={savingRemark}
                          >
                            {savingRemark
                              ? (
                                <LoaderCircle
                                  size={14}
                                  className="odc-spin"
                                />
                              )
                              : <Save size={14} />
                            }

                            Save
                          </button>

                          <button
                            type="button"
                            className="odc-cancel-remark"
                            onClick={cancelEditingRemark}
                            disabled={savingRemark}
                          >
                            <X size={14} />
                            Cancel
                          </button>

                        </div>
                      </div>

                    ) : (

                      <div className="odc-remark-display">

                        <span>
                          {employee.remarks || (
                            employee.distinct_log_days
                              ? '—'
                              : (
                                <span className="odc-muted">
                                  No matching ODC logs
                                </span>
                              )
                          )}
                        </span>

                        <button
                          type="button"
                          className="odc-edit-remark"
                          title={`Edit remarks for ${employee.emp_id}`}
                          aria-label={`Edit remarks for ${employee.emp_id}`}
                          onClick={() => startEditingRemark(employee)}
                        >
                          <Pencil size={14} />
                          Edit
                        </button>

                      </div>

                    )}

                  </td>

                </tr>

              ))}

              {!summary.employees?.length && (
                <tr>
                  <td colSpan="8" className="odc-empty">
                    No roster data yet. Upload your ODC workbook to begin.
                  </td>
                </tr>
              )}

            </tbody>

          </table>

        </div>

      )}


      {/* =================================================
          ODC LOGS
      ================================================= */}

      {tab === 'logs' && (
        <>

          <div className="odc-log-filters">

            <label>
              Employee ID

              <select
                value={logEmployee}
                onChange={(event) => {
                  setLogEmployee(event.target.value)
                }}
              >
                <option value="">All employees</option>

                {(summary.employees || []).map((employee) => (
                  <option
                    key={employee.emp_id}
                    value={employee.emp_id}
                  >
                    {employee.emp_id} — {employee.name || 'Unknown'}
                  </option>
                ))}
              </select>
            </label>


            <label>
              From

              <input
                type="date"
                value={startDate}
                onChange={(event) => {
                  setStartDate(event.target.value)
                }}
              />
            </label>


            <label>
              To

              <input
                type="date"
                value={endDate}
                onChange={(event) => {
                  setEndDate(event.target.value)
                }}
              />
            </label>


            <button
              type="button"
              onClick={clearLogFilters}
            >
              Clear log filters
            </button>

          </div>


          <div className="odc-table-wrap">

            <table className="odc-table">

              <thead>
                <tr>
                  <th>Emp ID</th>
                  <th>Employee name</th>
                  <th>LOB</th>
                  <th>DM Name</th>
                  <th>Log date</th>
                  <th>Work count</th>
                </tr>
              </thead>

              <tbody>

                {logs.map((log) => (
                  <tr key={log.id}>

                    <td className="odc-id">
                      {log.emp_id}
                    </td>

                    <td>
                      {log.emp_name || '—'}
                    </td>

                    <td>
                      {log.lob || '—'}
                    </td>

                    <td>
                      {log.dm_name || '—'}
                    </td>

                    <td>
                      {log.log_date || '—'}
                    </td>

                    <td>
                      {log.work_count || '—'}
                    </td>

                  </tr>
                ))}

                {!logs.length && (
                  <tr>
                    <td colSpan="6" className="odc-empty">
                      No ODC log records match these filters.
                    </td>
                  </tr>
                )}

              </tbody>

            </table>

          </div>

        </>
      )}


      {/* =================================================
          UPLOAD HISTORY
      ================================================= */}

      {tab === 'uploads' && (

        <div className="odc-table-wrap">

          <table className="odc-table">

            <thead>
              <tr>
                <th>Upload ID</th>
                <th>Filename</th>
                <th>Uploaded at</th>
                <th>Input rows</th>
                <th>New log rows</th>
                <th>Roster rows processed</th>
                <th>Unmatched IDs</th>
                <th>Warnings</th>
              </tr>
            </thead>

            <tbody>

              {uploads.map((uploadItem) => (

                <tr key={uploadItem.id}>

                  <td>
                    {uploadItem.id}
                  </td>

                  <td>
                    {uploadItem.filename}
                  </td>

                  <td>
                    {uploadItem.uploaded_at
                      ? new Date(
                          uploadItem.uploaded_at
                        ).toLocaleString()
                      : '—'}
                  </td>

                  <td>
                    {uploadItem.total_rows}
                  </td>

                  <td>
                    {uploadItem.inserted_logs}
                  </td>

                  <td>
                    {uploadItem.updated_employees}
                  </td>

                  <td>
                    {uploadItem.unmatched_logs}
                  </td>

                  <td>
                    {uploadItem.errors?.length || 0}
                  </td>

                </tr>

              ))}

              {!uploads.length && (
                <tr>
                  <td colSpan="8" className="odc-empty">
                    No uploads recorded yet.
                  </td>
                </tr>
              )}

            </tbody>

          </table>


          {uploads.some((item) => item.errors?.length) && (

            <div className="odc-warnings">

              <strong>
                Recent upload warnings
              </strong>

              {uploads
                .filter((item) => item.errors?.length)
                .slice(0, 3)
                .map((item) => (

                  <div key={item.id}>

                    <b>
                      {item.filename}
                    </b>

                    <ul>
                      {item.errors.slice(0, 8).map(
                        (warning, index) => (
                          <li key={index}>
                            {warning}
                          </li>
                        )
                      )}
                    </ul>

                  </div>

                ))}

            </div>

          )}

        </div>

      )}


      {/* DATA SAFETY NOTE */}

      <p className="odc-footnote">

        <Database size={13} />

        ODC data is isolated in

        <code>odc_employees</code>,

        <code>odc_employee_remarks</code>,

        <code>odc_logs</code> and

        <code>odc_uploads</code>.

        Refresh only reads these records. Reset ODC Data deletes
        only these ODC tables and never calls the attendance reset endpoint.

      </p>


      {/* =================================================
          RESET CONFIRMATION POPUP
      ================================================= */}

      {showResetConfirm && (

        <div
          className="odc-modal-backdrop"
          role="presentation"
        >

          <div
            className="odc-confirm-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="odc-reset-title"
          >

            <div className="odc-confirm-icon">
              <AlertTriangle size={23} />
            </div>

            <h2 id="odc-reset-title">
              Reset ODC data?
            </h2>

            <p>
              This permanently deletes ODC employees, ODC logs,
              ODC upload history and manually edited ODC remarks.
            </p>

            <p className="odc-confirm-safe">
              Your attendance employees, attendance records and
              attendance upload history will not be changed.
            </p>

            <div className="odc-confirm-actions">

              <button
                type="button"
                className="odc-cancel-button"
                onClick={() => setShowResetConfirm(false)}
                disabled={resetting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="odc-confirm-reset"
                onClick={resetODCData}
                disabled={resetting}
              >
                {resetting
                  ? (
                    <LoaderCircle
                      size={15}
                      className="odc-spin"
                    />
                  )
                  : <Trash2 size={15} />
                }

                {resetting
                  ? 'Resetting…'
                  : 'Yes, reset ODC data'}
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  )
}
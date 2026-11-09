import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

const API_BASE = '/api/org'

function OrganizationHierarchyPage() {
  const [hierarchy, setHierarchy] = useState([])
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [collapsedNodes, setCollapsedNodes] = useState(new Set())

  const collectHierarchyIds = (nodes) => {
    const ids = []

    const walk = (items) => {
      items.forEach((node) => {
        const employee = node?.employee || {}
        const empId = employee['EMPLOYEE NUMBER']
        if (empId && node?.children?.length) {
          ids.push(String(empId))
        }
        if (node?.children?.length) walk(node.children)
      })
    }

    walk(nodes)
    return ids
  }

  const expandAll = () => setCollapsedNodes(new Set())

  const collapseAll = () => {
    setCollapsedNodes(new Set(collectHierarchyIds(hierarchy)))
  }

  const toggleNode = (employeeNumber) => {
    setCollapsedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(String(employeeNumber))) {
        next.delete(String(employeeNumber))
      } else {
        next.add(String(employeeNumber))
      }
      return next
    })
  }

  const flattenEmployees = useMemo(() => {
    const employees = []
    const stack = [...hierarchy]

    while (stack.length) {
      const node = stack.pop()
      employees.push(node.employee)
      if (node.children?.length) stack.push(...node.children)
    }

    return employees
  }, [hierarchy])

  const loadHierarchy = async () => {
    try {
      const response = await axios.get(`${API_BASE}/hierarchy`)
      const data = response.data || []
      setHierarchy(data)
      setSelectedEmployee(null)
      setCollapsedNodes(new Set())
      setError('')
    } catch (err) {
      console.error('Load hierarchy failed', err)
      setError('Unable to load organization hierarchy.')
    }
  }

  useEffect(() => {
    loadHierarchy()
  }, [])

  const uploadHierarchy = async () => {
    if (!file) {
      setError('Please select an Excel file first.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      setError('')
      const response = await axios.post(`${API_BASE}/upload-org`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const data = response.data || []
      setHierarchy(data)
      setSelectedEmployee(null)
      setCollapsedNodes(new Set())
      setFile(null)
    } catch (err) {
      console.error('Upload failed', err)
      setError(err?.response?.data?.detail || 'Unable to upload hierarchy file.')
    } finally {
      setLoading(false)
    }
  }

  const renderNode = (node, level = 0) => {
    const employee = node.employee || {}
    const employeeNumber = employee['EMPLOYEE NUMBER']
    const childCount = node.children?.length || 0
    const hasChildren = childCount > 0
    const isCollapsed = hasChildren && collapsedNodes.has(String(employeeNumber))

    return (
      <div key={employeeNumber || `node-${level}`} className="org-tree-node-wrap" style={{ marginLeft: level * 18 }}>
        <div className="org-tree-row">
          {level > 0 && <span className="tree-connector" aria-hidden="true" />}
          {hasChildren && (
            <button
              type="button"
              className="org-toggle-btn"
              onClick={() => toggleNode(employeeNumber)}
              aria-label={isCollapsed ? `Expand ${employee['EMPLOYEE NAME']}` : `Collapse ${employee['EMPLOYEE NAME']}`}
            >
              {isCollapsed ? '▸' : '▾'}
            </button>
          )}
          {!hasChildren && <span className="org-toggle-placeholder" aria-hidden="true" />}
          <button
            type="button"
            className={`org-tree-node ${selectedEmployee?.['EMPLOYEE NUMBER'] === employeeNumber ? 'selected' : ''}`}
            onClick={() => setSelectedEmployee(employee)}
          >
            <div className="org-avatar">
              <img src={employee.PROFILE || 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'} alt={employee['EMPLOYEE NAME']} />
            </div>
            <div className="org-node-details">
              <strong>{employee['EMPLOYEE NAME'] || 'Unnamed Employee'}</strong>
              <span>{employee.DESIGNATION || 'No designation'}</span>
              <small>{employeeNumber || 'N/A'}</small>
            </div>
            {hasChildren && <span className="org-child-count">{childCount}</span>}
          </button>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="org-tree-children">
            {node.children.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="org-page-shell">
      <div className="org-page-header">
        <div>
          <h1>Organization Hierarchy</h1>
          <p>Upload an Excel sheet to build the reporting structure and visualize the organization tree.</p>
        </div>
      </div>

      <div className="org-toolbar">
        <input type="file" accept=".xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button type="button" className="primary-btn" onClick={uploadHierarchy} disabled={loading}>
          {loading ? 'Uploading...' : 'Upload Excel'}
        </button>
        <button type="button" className="secondary-btn" onClick={loadHierarchy}>Refresh</button>

        {hierarchy.length > 0 && (
          <div className="org-tree-controls">
            <button type="button" className="secondary-btn" onClick={expandAll}>Expand All</button>
            <button type="button" className="secondary-btn" onClick={collapseAll}>Collapse All</button>
          </div>
        )}
      </div>

      {error && <div className="org-error-box">{error}</div>}

      <div className="org-layout">
        <div className="org-panel">
          <div className="org-panel-header">Hierarchy Tree</div>
          {hierarchy.length > 0 ? (
            <div className="org-tree-view">{hierarchy.map((node) => renderNode(node))}</div>
          ) : (
            <div className="org-empty-state">No organization data loaded yet.</div>
          )}
        </div>

        <div className="org-panel">
          <div className="org-panel-header">Employee Details</div>
          {selectedEmployee ? (
            <div className="org-details-grid">
              <img className="org-profile" src={selectedEmployee.PROFILE || 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'} alt={selectedEmployee['EMPLOYEE NAME']} />
              <div className="org-detail-row"><span>Name</span><strong>{selectedEmployee['EMPLOYEE NAME']}</strong></div>
              <div className="org-detail-row"><span>Employee Number</span><strong>{selectedEmployee['EMPLOYEE NUMBER']}</strong></div>
              <div className="org-detail-row"><span>Designation</span><strong>{selectedEmployee.DESIGNATION || '—'}</strong></div>
              <div className="org-detail-row"><span>Manager ID</span><strong>{selectedEmployee['MANAGER ID'] || '—'}</strong></div>
              <div className="org-detail-row"><span>Email</span><strong>{selectedEmployee['EMAIL ADDRESS'] || '—'}</strong></div>
              <div className="org-detail-row"><span>Location</span><strong>{selectedEmployee.LOCATION || '—'}</strong></div>
              <div className="org-detail-row"><span>Gender</span><strong>{selectedEmployee.GENDER || '—'}</strong></div>
            </div>
          ) : (
            <div className="org-empty-state">Select an employee from the hierarchy tree.</div>
          )}
        </div>
      </div>

      {flattenEmployees.length > 0 && (
        <div className="org-employee-summary">
          <strong>{flattenEmployees.length}</strong> employees in hierarchy
        </div>
      )}
    </div>
  )
}

export default OrganizationHierarchyPage

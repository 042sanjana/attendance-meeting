import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

const API_BASE = '/api/org'
const NODE_WIDTH = 220
const NODE_HEIGHT = 88
const HORIZONTAL_GAP = 120
const VERTICAL_GAP = 170
const TREE_TOP_OFFSET = 30
const TREE_LEFT_OFFSET = 60

const getNodeKey = (node, fallback = 'node') => {
  const employee = node?.employee || {}
  const employeeNumber = employee['EMPLOYEE NUMBER']
  if (employeeNumber) return String(employeeNumber)
  return `${fallback}-${employee['EMPLOYEE NAME'] || 'unnamed'}`
}

const buildVisibleHierarchy = (nodes, collapsedNodes) => {
  const walk = (items) =>
    items.map((node) => {
      const employeeNumber = String(node?.employee?.['EMPLOYEE NUMBER'] || '')
      const isCollapsed = employeeNumber && collapsedNodes.has(employeeNumber)

      return {
        ...node,
        children: isCollapsed ? [] : walk(node?.children || []),
      }
    })

  return walk(nodes)
}

const getSubtreeWidth = (node) => {
  const children = node.children || []
  if (!children.length) return NODE_WIDTH

  const totalChildWidth = children.reduce((sum, child) => sum + getSubtreeWidth(child), 0)
  return totalChildWidth + (children.length - 1) * HORIZONTAL_GAP
}

const layoutTree = (nodes) => {
  const flatNodes = []

  const placeNode = (node, depth, startX, fallbackKey) => {
    const key = getNodeKey(node, fallbackKey)
    const subtreeWidth = getSubtreeWidth(node)
    const centerX = startX + subtreeWidth / 2
    const y = depth * VERTICAL_GAP + TREE_TOP_OFFSET

    flatNodes.push({
      ...node.employee,
      _key: key,
      _depth: depth,
      _x: centerX,
      _y: y,
      _childrenCount: node.children?.length || 0,
    })

    if (!node.children?.length) return

    let childStartX = startX
    node.children.forEach((child, index) => {
      const childKey = getNodeKey(child, `${key}-child-${index}`)
      placeNode(child, depth + 1, childStartX, childKey)
      childStartX += getSubtreeWidth(child) + HORIZONTAL_GAP
    })
  }

  let cursorX = TREE_LEFT_OFFSET
  nodes.forEach((node, index) => {
    placeNode(node, 0, cursorX, `root-${index}`)
    cursorX += getSubtreeWidth(node) + HORIZONTAL_GAP
  })

  const totalWidth = Math.max(
    ...flatNodes.map((node) => node._x + NODE_WIDTH / 2 + TREE_LEFT_OFFSET),
    0,
  ) + 80
  const totalHeight = Math.max(
    ...flatNodes.map((node) => node._y + NODE_HEIGHT + 40),
    420,
  )

  return { flatNodes, totalWidth, totalHeight }
}

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

  const visibleHierarchy = useMemo(
    () => buildVisibleHierarchy(hierarchy, collapsedNodes),
    [hierarchy, collapsedNodes],
  )

  const treeLayout = useMemo(() => layoutTree(visibleHierarchy), [visibleHierarchy])

  const findNodeByEmployeeNumber = (nodes, employeeNumber) => {
    if (!employeeNumber) return null

    const stack = [...nodes]
    while (stack.length) {
      const node = stack.pop()
      if (String(node?.employee?.['EMPLOYEE NUMBER']) === String(employeeNumber)) {
        return node
      }
      if (node?.children?.length) {
        stack.push(...node.children)
      }
    }

    return null
  }

  const getChildrenCountForEmployee = (employeeNumber) => {
    const node = findNodeByEmployeeNumber(hierarchy, employeeNumber)
    return node?.children?.length || 0
  }

  const toggleNode = (employeeNumber) => {
    const node = findNodeByEmployeeNumber(hierarchy, employeeNumber)
    if (!node || !node.children?.length) return

    setCollapsedNodes((prev) => {
      const next = new Set(prev)
      const key = String(employeeNumber)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const nodeMap = useMemo(() => {
    const map = new Map()
    treeLayout.flatNodes.forEach((employee) => {
      map.set(String(employee._key), { x: employee._x, y: employee._y })
    })
    return map
  }, [treeLayout.flatNodes])

  const connectors = useMemo(() => {
    const paths = []

    const walk = (node, parent = null) => {
      if (!node) return

      if (parent) {
        const parentKey = getNodeKey(parent, 'parent')
        const childKey = getNodeKey(node, 'child')
        const parentPos = nodeMap.get(parentKey)
        const childPos = nodeMap.get(childKey)

        if (parentPos && childPos) {
          const startX = parentPos.x
          const startY = parentPos.y + NODE_HEIGHT
          const endX = childPos.x
          const endY = childPos.y
          const midY = startY + (endY - startY) / 2

          paths.push(`M ${startX} ${startY} V ${midY} H ${endX} V ${endY}`)
        }
      }

      if (node.children?.length) {
        node.children.forEach((child) => walk(child, node))
      }
    }

    visibleHierarchy.forEach((root) => walk(root))
    return paths
  }, [nodeMap, visibleHierarchy])

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

  const renderNode = (employee) => {
    const employeeNumber = employee['EMPLOYEE NUMBER']
    const childCount = getChildrenCountForEmployee(employeeNumber)
    const hasChildren = childCount > 0
    const isCollapsed = hasChildren && collapsedNodes.has(String(employeeNumber))
    const isSelected = selectedEmployee?.['EMPLOYEE NUMBER'] === employeeNumber

    return (
      <div
        key={employee._key}
        className="org-node-shell"
        style={{
          left: `${employee._x - NODE_WIDTH / 2}px`,
          top: `${employee._y}px`,
        }}
      >
        {hasChildren && (
          <button
            type="button"
            className="org-toggle-btn"
            aria-expanded={!isCollapsed}
            onClick={(event) => {
              event.stopPropagation()
              toggleNode(employeeNumber)
            }}
            aria-label={isCollapsed ? `Expand ${employee['EMPLOYEE NAME']}` : `Collapse ${employee['EMPLOYEE NAME']}`}
          >
            {isCollapsed ? '▸' : '▾'}
          </button>
        )}
        {!hasChildren && <span className="org-toggle-placeholder" aria-hidden="true" />}

        <button
          type="button"
          className={`org-tree-node ${isSelected ? 'selected' : ''}`}
          onClick={() => setSelectedEmployee(employee)}
        >
          <div className="org-avatar">
            <img
              src={employee.PROFILE || 'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'}
              alt={employee['EMPLOYEE NAME']}
            />
          </div>

          <div className="org-node-details">
            <strong>{employee['EMPLOYEE NAME'] || 'Unnamed Employee'}</strong>
            <span>{employee.DESIGNATION || 'No designation'}</span>
            <small>{employeeNumber || 'N/A'}</small>
          </div>

          {hasChildren && <span className="org-child-count">{childCount}</span>}
        </button>
      </div>
    )
  }

  return (
    <div className="org-page-shell">
      <div className="org-page-header">
        <div>
          <h1>Organization Hierarchy</h1>
          <p>CEO at the top, managers in the next level, and their teams below in a traditional top-down hierarchy.</p>
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
          {visibleHierarchy.length > 0 ? (
            <div className="org-tree-scroll">
              <div
                className="org-tree-canvas"
                style={{
                  width: `${treeLayout.totalWidth}px`,
                  height: `${treeLayout.totalHeight}px`,
                }}
              >
                <svg
                  className="org-tree-links"
                  width={treeLayout.totalWidth}
                  height={treeLayout.totalHeight}
                  preserveAspectRatio="xMinYMin meet"
                >
                  {connectors.map((path, index) => (
                    <path key={`connector-${index}`} d={path} />
                  ))}
                </svg>

                {treeLayout.flatNodes.map((employee) => renderNode(employee))}
              </div>
            </div>
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

import { useState, useMemo } from 'react'
import type { ReconResult } from './ReconGraph'
import './ReconList.css'

interface ReconListProps {
  results: ReconResult[]
  onResultSelect: (result: ReconResult | null) => void
}

type SortField = 'path' | 'status_code' | 'content_type' | 'content_length'
type SortDirection = 'asc' | 'desc'

function ReconList({ results, onResultSelect }: ReconListProps) {
  const [sortField, setSortField] = useState<SortField>('path')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const sortedResults = useMemo(() => {
    const sorted = [...results].sort((a, b) => {
      let aVal: any = a[sortField]
      let bVal: any = b[sortField]

      // Handle null values
      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1

      // String comparison for path and content_type
      if (sortField === 'path' || sortField === 'content_type') {
        aVal = String(aVal).toLowerCase()
        bVal = String(bVal).toLowerCase()
        return sortDirection === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }

      // Numeric comparison for status_code and content_length
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    })

    return sorted
  }, [results, sortField, sortDirection])

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const getStatusClass = (status: number | null): string => {
    if (!status) return ''
    if (status >= 200 && status < 300) return 'success'
    if (status >= 300 && status < 400) return 'redirect'
    if (status >= 400 && status < 500) return 'client-error'
    if (status >= 500) return 'server-error'
    return ''
  }

  const formatSize = (bytes: number | null): string => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const SortIndicator = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className="sort-indicator">↕</span>
    return <span className="sort-indicator active">{sortDirection === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div className="recon-list">
      <div className="recon-list-header">
        <span className="result-count">{results.length} paths decouverts</span>
      </div>

      <table className="recon-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('path')} className="sortable">
              Path <SortIndicator field="path" />
            </th>
            <th onClick={() => handleSort('status_code')} className="sortable col-status">
              Status <SortIndicator field="status_code" />
            </th>
            <th onClick={() => handleSort('content_type')} className="sortable col-content-type">
              Content-Type <SortIndicator field="content_type" />
            </th>
            <th onClick={() => handleSort('content_length')} className="sortable col-size">
              Taille <SortIndicator field="content_length" />
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedResults.map((result) => (
            <tr
              key={result.id}
              className="result-row"
              onClick={() => onResultSelect(result)}
            >
              <td className="path-cell">
                <code>{result.path}</code>
              </td>
              <td className="status-cell">
                <span className={`status-badge ${getStatusClass(result.status_code)}`}>
                  {result.status_code || '-'}
                </span>
              </td>
              <td className="content-type-cell">
                <code className="content-type">{result.content_type || '-'}</code>
              </td>
              <td className="size-cell">
                {formatSize(result.content_length)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {results.length === 0 && (
        <div className="empty-state">
          <p>Aucun resultat disponible</p>
          <p className="hint">Lancez un scan pour voir les resultats</p>
        </div>
      )}
    </div>
  )
}

export default ReconList

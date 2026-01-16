import { useMemo, useEffect, useState, useCallback, useRef } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
  Panel,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react'
import type { Node, Edge, NodeMouseHandler } from '@xyflow/react'
import { toPng } from 'html-to-image'
import '@xyflow/react/dist/style.css'
import './ReconGraph.css'

// Types
export interface ReconResult {
  id: number
  path: string
  status_code: number | null
  content_type: string | null
  content_length?: number | null
  parent_path: string | null
}

interface ReconGraphProps {
  results: ReconResult[]
  onNodeSelect?: (result: ReconResult | null) => void
  onExportImage?: (imageBlob: Blob) => void
}

// Constantes de layout
const LEVEL_WIDTH = 220
const NODE_HEIGHT = 60
const START_X = 50
const START_Y = 80

// Couleur selon le status code
function getStatusColor(status: number | null): string {
  if (!status) return '#6e7681'
  if (status >= 200 && status < 300) return '#1a7f37'
  if (status >= 300 && status < 400) return '#0969da'
  if (status >= 400 && status < 500) return '#9a6700'
  if (status >= 500) return '#cf222e'
  return '#6e7681'
}

// Categorie de status pour les filtres
function getStatusCategory(status: number | null): string {
  if (!status) return 'unknown'
  if (status >= 200 && status < 300) return '2xx'
  if (status >= 300 && status < 400) return '3xx'
  if (status >= 400 && status < 500) return '4xx'
  if (status >= 500) return '5xx'
  return 'unknown'
}

// Calculer la profondeur d'un path
function getPathDepth(path: string): number {
  if (path === '/') return 0
  return path.split('/').filter(p => p !== '').length
}

// Extraire le nom court du path
function getPathName(path: string): string {
  if (path === '/') return '/'
  const parts = path.split('/').filter(p => p !== '')
  return '/' + parts[parts.length - 1]
}

// Calculer les statistiques
function computeStats(results: ReconResult[]) {
  const stats = {
    total: results.length,
    success: 0,    // 2xx
    redirect: 0,   // 3xx
    clientError: 0, // 4xx
    serverError: 0, // 5xx
    unknown: 0
  }

  results.forEach(r => {
    const cat = getStatusCategory(r.status_code)
    if (cat === '2xx') stats.success++
    else if (cat === '3xx') stats.redirect++
    else if (cat === '4xx') stats.clientError++
    else if (cat === '5xx') stats.serverError++
    else stats.unknown++
  })

  return stats
}

// Convertir les resultats en noeuds et edges
function resultsToGraph(
  results: ReconResult[],
  selectedId: number | null
): { nodes: Node[], edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []
  const pathToId: Map<string, string> = new Map()

  // Grouper par niveau de profondeur
  const levelGroups: Map<number, ReconResult[]> = new Map()
  let maxDepth = 0

  results.forEach(result => {
    const depth = getPathDepth(result.path)
    maxDepth = Math.max(maxDepth, depth)

    if (!levelGroups.has(depth)) {
      levelGroups.set(depth, [])
    }
    levelGroups.get(depth)!.push(result)
  })

  // Trier chaque niveau alphabetiquement
  levelGroups.forEach((group) => {
    group.sort((a, b) => a.path.localeCompare(b.path))
  })

  // Creer les noeuds niveau par niveau
  for (let depth = 0; depth <= maxDepth; depth++) {
    const levelResults = levelGroups.get(depth) || []

    levelResults.forEach((result, indexInLevel) => {
      const nodeId = `node-${result.id}`
      pathToId.set(result.path, nodeId)

      const statusColor = getStatusColor(result.status_code)
      const isSelected = result.id === selectedId

      nodes.push({
        id: nodeId,
        type: 'default',
        position: {
          x: START_X + depth * LEVEL_WIDTH,
          y: START_Y + indexInLevel * NODE_HEIGHT
        },
        data: {
          label: (
            <div className="node-content">
              <span className="node-path">{getPathName(result.path)}</span>
              {result.status_code && (
                <span className="node-status" style={{ backgroundColor: statusColor }}>
                  {result.status_code}
                </span>
              )}
            </div>
          ),
          result: result
        },
        style: {
          border: isSelected ? `3px solid ${statusColor}` : `2px solid ${statusColor}`,
          borderRadius: '6px',
          padding: '6px 10px',
          background: isSelected ? '#f0f7ff' : '#ffffff',
          fontSize: '12px',
          minWidth: '100px',
          boxShadow: isSelected ? '0 0 8px rgba(9, 105, 218, 0.4)' : 'none',
          cursor: 'pointer'
        }
      })

      // Creer l'edge vers le parent
      if (result.parent_path && pathToId.has(result.parent_path)) {
        const parentId = pathToId.get(result.parent_path)!
        edges.push({
          id: `edge-${parentId}-${nodeId}`,
          source: parentId,
          target: nodeId,
          type: 'smoothstep',
          style: { stroke: '#d0d7de', strokeWidth: 1.5 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: '#d0d7de',
            width: 15,
            height: 15
          }
        })
      }
    })
  }

  return { nodes, edges }
}

// Composant interne avec acces a useReactFlow
function ReconGraphInner({ results, onNodeSelect, onExportImage }: ReconGraphProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { getNodes } = useReactFlow()

  // Etats locaux
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  // Filtrer les resultats
  const filteredResults = useMemo(() => {
    return results.filter(r => {
      // Filtre par recherche
      if (searchQuery && !r.path.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      // Filtre par status
      if (statusFilter && getStatusCategory(r.status_code) !== statusFilter) {
        return false
      }
      return true
    })
  }, [results, searchQuery, statusFilter])

  // Stats sur les resultats complets (pas filtres)
  const stats = useMemo(() => computeStats(results), [results])

  // Convertir en graphe
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => resultsToGraph(filteredResults, selectedNodeId),
    [filteredResults, selectedNodeId]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Mise a jour quand les resultats ou filtres changent
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = resultsToGraph(filteredResults, selectedNodeId)
    setNodes(newNodes)
    setEdges(newEdges)
  }, [filteredResults, selectedNodeId, setNodes, setEdges])

  // Gestion du clic sur un noeud
  const handleNodeClick: NodeMouseHandler = useCallback((_, node) => {
    const result = node.data.result as ReconResult
    if (selectedNodeId === result.id) {
      // Deselectionner si deja selectionne
      setSelectedNodeId(null)
      onNodeSelect?.(null)
    } else {
      setSelectedNodeId(result.id)
      onNodeSelect?.(result)
    }
  }, [selectedNodeId, onNodeSelect])

  // Export en image PNG
  const handleExport = useCallback(async () => {
    if (!reactFlowWrapper.current || isExporting) return

    setIsExporting(true)
    try {
      // Trouver l'element React Flow
      const flowElement = reactFlowWrapper.current.querySelector('.react-flow') as HTMLElement
      if (!flowElement) return

      const dataUrl = await toPng(flowElement, {
        backgroundColor: '#ffffff',
        quality: 1,
        pixelRatio: 2
      })

      // Convertir en Blob
      const response = await fetch(dataUrl)
      const blob = await response.blob()

      // Callback pour sauvegarder
      if (onExportImage) {
        onExportImage(blob)
      } else {
        // Telecharger directement
        const link = document.createElement('a')
        link.download = `recon-graph-${Date.now()}.png`
        link.href = dataUrl
        link.click()
      }
    } catch (error) {
      console.error('Erreur export:', error)
    } finally {
      setIsExporting(false)
    }
  }, [isExporting, onExportImage])

  // Reset des filtres
  const resetFilters = () => {
    setSearchQuery('')
    setStatusFilter(null)
  }

  if (results.length === 0) {
    return (
      <div className="recon-graph-empty">
        <p>Aucun resultat de scan</p>
        <p className="hint">Lancez un scan pour voir l'arborescence</p>
      </div>
    )
  }

  return (
    <div className="recon-graph-container">
      {/* Barre de stats */}
      <div className="recon-stats">
        <div className="stat-item total">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat-item success">
          <span className="stat-value">{stats.success}</span>
          <span className="stat-label">2xx</span>
        </div>
        <div className="stat-item redirect">
          <span className="stat-value">{stats.redirect}</span>
          <span className="stat-label">3xx</span>
        </div>
        <div className="stat-item client-error">
          <span className="stat-value">{stats.clientError}</span>
          <span className="stat-label">4xx</span>
        </div>
        <div className="stat-item server-error">
          <span className="stat-value">{stats.serverError}</span>
          <span className="stat-label">5xx</span>
        </div>
      </div>

      {/* Barre de filtres */}
      <div className="recon-filters">
        <div className="filter-search">
          <input
            type="text"
            placeholder="Rechercher un path..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="filter-status">
          <button
            className={`filter-btn ${statusFilter === null ? 'active' : ''}`}
            onClick={() => setStatusFilter(null)}
          >
            Tous
          </button>
          <button
            className={`filter-btn success ${statusFilter === '2xx' ? 'active' : ''}`}
            onClick={() => setStatusFilter(statusFilter === '2xx' ? null : '2xx')}
          >
            2xx
          </button>
          <button
            className={`filter-btn redirect ${statusFilter === '3xx' ? 'active' : ''}`}
            onClick={() => setStatusFilter(statusFilter === '3xx' ? null : '3xx')}
          >
            3xx
          </button>
          <button
            className={`filter-btn client-error ${statusFilter === '4xx' ? 'active' : ''}`}
            onClick={() => setStatusFilter(statusFilter === '4xx' ? null : '4xx')}
          >
            4xx
          </button>
          <button
            className={`filter-btn server-error ${statusFilter === '5xx' ? 'active' : ''}`}
            onClick={() => setStatusFilter(statusFilter === '5xx' ? null : '5xx')}
          >
            5xx
          </button>
        </div>
        <button className="export-btn" onClick={handleExport} disabled={isExporting}>
          {isExporting ? 'Export...' : 'Exporter PNG'}
        </button>
      </div>

      {/* Info filtre actif */}
      {(searchQuery || statusFilter) && (
        <div className="filter-info">
          <span>
            {filteredResults.length} / {results.length} resultats affiches
          </span>
          <button className="clear-filters" onClick={resetFilters}>
            Effacer les filtres
          </button>
        </div>
      )}

      {/* Graphe */}
      <div className="recon-graph" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          attributionPosition="bottom-left"
          minZoom={0.3}
          maxZoom={1.5}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} color="#e0e0e0" />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const result = node.data?.result as ReconResult | undefined
              return getStatusColor(result?.status_code ?? null)
            }}
            maskColor="rgba(0, 0, 0, 0.08)"
            style={{ background: '#fafafa' }}
          />

          {/* Legende integree */}
          <Panel position="bottom-left" className="graph-legend-panel">
            <div className="graph-legend">
              <span className="legend-item">
                <span className="legend-dot" style={{ background: '#1a7f37' }}></span>
                2xx
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{ background: '#0969da' }}></span>
                3xx
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{ background: '#9a6700' }}></span>
                4xx
              </span>
              <span className="legend-item">
                <span className="legend-dot" style={{ background: '#cf222e' }}></span>
                5xx
              </span>
            </div>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  )
}

// Composant wrapper avec Provider
function ReconGraph(props: ReconGraphProps) {
  return (
    <ReactFlowProvider>
      <ReconGraphInner {...props} />
    </ReactFlowProvider>
  )
}

export default ReconGraph

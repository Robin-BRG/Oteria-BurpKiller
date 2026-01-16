import { useMemo } from 'react'
import './EnumDisplay.css'

export interface EnumResult {
  id: number
  result_type: string
  category: string
  name: string
  value: string | null
  confidence: string
  security_level: string | null
  description: string
}

interface EnumDisplayProps {
  results: EnumResult[]
}

function EnumDisplay({ results }: EnumDisplayProps) {
  // Grouper les resultats par type
  const groupedResults = useMemo(() => {
    const groups: Record<string, EnumResult[]> = {
      technologies: [],
      securityHeaders: [],
      infoHeaders: [],
      errors: []
    }

    results.forEach(result => {
      if (result.result_type === 'technology') {
        groups.technologies.push(result)
      } else if (result.result_type === 'header' && result.category === 'Security') {
        groups.securityHeaders.push(result)
      } else if (result.result_type === 'header' && result.category === 'Information') {
        groups.infoHeaders.push(result)
      } else if (result.result_type === 'error') {
        groups.errors.push(result)
      }
    })

    return groups
  }, [results])

  // Grouper les technologies par categorie
  const technologiesByCategory = useMemo(() => {
    const categories: Record<string, EnumResult[]> = {}
    groupedResults.technologies.forEach(tech => {
      if (!categories[tech.category]) {
        categories[tech.category] = []
      }
      categories[tech.category].push(tech)
    })
    return categories
  }, [groupedResults.technologies])

  const getSecurityLevelClass = (level: string | null): string => {
    if (!level) return ''
    switch (level) {
      case 'secure': return 'level-secure'
      case 'warning': return 'level-warning'
      case 'missing': return 'level-missing'
      case 'insecure': return 'level-insecure'
      default: return ''
    }
  }

  const getSecurityLevelLabel = (level: string | null): string => {
    if (!level) return ''
    switch (level) {
      case 'secure': return 'Securise'
      case 'warning': return 'Attention'
      case 'missing': return 'Manquant'
      case 'insecure': return 'Risque'
      default: return level
    }
  }

  const getConfidenceBadge = (confidence: string) => {
    return (
      <span className={`confidence-badge confidence-${confidence}`}>
        {confidence === 'high' ? 'Haute confiance' : confidence === 'medium' ? 'Confiance moyenne' : 'Faible confiance'}
      </span>
    )
  }

  if (results.length === 0) {
    return (
      <div className="enum-display">
        <div className="empty-state">
          <p>Aucun resultat disponible</p>
          <p className="hint">Lancez un scan pour voir les resultats</p>
        </div>
      </div>
    )
  }

  return (
    <div className="enum-display">
      {/* Erreurs */}
      {groupedResults.errors.length > 0 && (
        <div className="enum-section error-section">
          <h3 className="section-title">Erreurs</h3>
          {groupedResults.errors.map(error => (
            <div key={error.id} className="error-item">
              <div className="error-name">{error.name}</div>
              <div className="error-desc">{error.description}</div>
            </div>
          ))}
        </div>
      )}

      {/* Technologies detectees */}
      {Object.keys(technologiesByCategory).length > 0 && (
        <div className="enum-section">
          <h3 className="section-title">Technologies detectees</h3>
          <div className="tech-grid">
            {Object.entries(technologiesByCategory).map(([category, techs]) => (
              <div key={category} className="tech-category">
                <div className="tech-category-title">{category}</div>
                <div className="tech-items">
                  {techs.map(tech => (
                    <div key={tech.id} className="tech-item">
                      <div className="tech-header">
                        <span className="tech-name">{tech.name}</span>
                        {tech.value && <span className="tech-version">v{tech.value}</span>}
                      </div>
                      <div className="tech-footer">
                        {getConfidenceBadge(tech.confidence)}
                        <span className="tech-desc">{tech.description}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Headers de securite */}
      {groupedResults.securityHeaders.length > 0 && (
        <div className="enum-section">
          <h3 className="section-title">Headers de securite</h3>
          <div className="headers-list">
            {groupedResults.securityHeaders.map(header => (
              <div key={header.id} className={`header-item ${getSecurityLevelClass(header.security_level)}`}>
                <div className="header-main">
                  <div className="header-name-row">
                    <code className="header-name">{header.name}</code>
                    {header.security_level && (
                      <span className={`security-badge ${getSecurityLevelClass(header.security_level)}`}>
                        {getSecurityLevelLabel(header.security_level)}
                      </span>
                    )}
                  </div>
                  {header.value && (
                    <code className="header-value">{header.value}</code>
                  )}
                </div>
                <p className="header-desc">{header.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Headers informatifs */}
      {groupedResults.infoHeaders.length > 0 && (
        <div className="enum-section">
          <h3 className="section-title">Headers informatifs</h3>
          <div className="info-headers-list">
            {groupedResults.infoHeaders.map(header => (
              <div key={header.id} className="info-header-item">
                <code className="info-header-name">{header.name}</code>
                <code className="info-header-value">{header.value}</code>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default EnumDisplay

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchRings } from '../api'
import { Search, AlertTriangle, Eye } from 'lucide-react'

function getRiskLevel(score) {
  if (score >= 80) return 'critical'
  if (score >= 60) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

function getRiskLabel(score) {
  if (score >= 80) return 'CRITICAL'
  if (score >= 60) return 'HIGH'
  if (score >= 40) return 'MEDIUM'
  return 'LOW'
}

export default function RingExplorer() {
  const [rings, setRings] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    fetchRings().then(d => { setRings(d.rings || []); setLoading(false) })
  }, [])

  if (loading) return <div><div className="spinner"></div><p className="loading-text">Loading rings...</p></div>

  const ringTypes = [...new Set(rings.map(r => r.ring_type))]

  const filtered = rings.filter(r => {
    const matchSearch = r.ring_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        r.ring_type.toLowerCase().includes(searchTerm.toLowerCase())
    const matchType = filterType === 'all' || r.ring_type === filterType
    return matchSearch && matchType
  })

  return (
    <div className="fade-in">
      <div className="page-header">
        <h2>🔍 Ring Explorer</h2>
        <p>Investigate {rings.length} detected abuse rings — click any ring for full analysis + LLM report</p>
      </div>

      {/* Filters */}
      <div className="panel" style={{display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap'}}>
        <div style={{position: 'relative', flex: 1, minWidth: 200}}>
          <Search size={16} style={{position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)'}} />
          <input
            type="text"
            placeholder="Search by ring ID or type..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%', padding: '10px 12px 10px 36px',
              background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 'var(--radius-sm)', color: '#fff',
              fontSize: 14, outline: 'none', boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.5)',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--accent-blue)'}
            onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
          />
        </div>
        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          style={{
            padding: '10px 16px', background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.1)', borderRadius: 'var(--radius-sm)',
            color: '#fff', fontSize: 14, cursor: 'pointer', outline: 'none',
            boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.5)',
          }}
        >
          <option value="all">All Types ({rings.length})</option>
          {ringTypes.map(t => (
            <option key={t} value={t}>{t} ({rings.filter(r => r.ring_type === t).length})</option>
          ))}
        </select>
      </div>

      {/* Rings table */}
      <div className="panel" style={{marginTop: 16}}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Ring ID</th>
              <th>Type</th>
              <th>Members</th>
              <th>Shared Devices</th>
              <th>Shared IPs</th>
              <th>Avg Refund Rate</th>
              <th>Risk Score</th>
              <th>Policy</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((ring, i) => {
              const level = getRiskLevel(ring.risk_score)
              return (
                <tr key={ring.ring_id} onClick={() => navigate(`/rings/${ring.ring_id}`)}
                  style={{animationDelay: `${i * 0.03}s`}} className="fade-in">
                  <td style={{fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600}}>
                    {ring.ring_id}
                  </td>
                  <td>
                    <span className={`badge ${ring.ring_type}`}>{ring.ring_type}</span>
                  </td>
                  <td>{ring.ring_size}</td>
                  <td>{ring.num_shared_devices}</td>
                  <td>{ring.num_shared_ips}</td>
                  <td style={{color: ring.avg_refund_rate > 0.2 ? 'var(--accent-red)' : 'var(--text-primary)'}}>
                    {(ring.avg_refund_rate * 100).toFixed(1)}%
                  </td>
                  <td>
                    <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                      <div className="risk-bar">
                        <div className={`risk-bar-fill ${level}`} style={{width: `${ring.risk_score}%`}}></div>
                      </div>
                      <span className={`badge ${level}`}>{ring.risk_score} — {getRiskLabel(ring.risk_score)}</span>
                    </div>
                  </td>
                  <td>
                    <span style={{
                      padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 700, letterSpacing: 0.5,
                      background: ring.action === 'HARD_BLOCK' ? 'rgba(239,68,68,0.15)' :
                                  ring.action === 'REVIEW' ? 'rgba(245,158,11,0.15)' :
                                  ring.action === 'STEP_UP_AUTH' ? 'rgba(59,130,246,0.15)' : 'rgba(16,185,129,0.15)',
                      color: ring.action === 'HARD_BLOCK' ? '#ef4444' :
                             ring.action === 'REVIEW' ? '#f59e0b' :
                             ring.action === 'STEP_UP_AUTH' ? '#3b82f6' : '#10b981',
                      border: `1px solid ${ring.action === 'HARD_BLOCK' ? 'rgba(239,68,68,0.3)' :
                                           ring.action === 'REVIEW' ? 'rgba(245,158,11,0.3)' :
                                           ring.action === 'STEP_UP_AUTH' ? 'rgba(59,130,246,0.3)' : 'rgba(16,185,129,0.3)'}`,
                    }}>
                      {ring.action?.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-outline" style={{padding: '6px 12px', fontSize: 12}}
                      onClick={e => { e.stopPropagation(); navigate(`/rings/${ring.ring_id}`) }}>
                      <Eye size={14} /> Investigate
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p style={{textAlign: 'center', padding: 40, color: 'var(--text-muted)'}}>
            No rings match your search.
          </p>
        )}
      </div>
    </div>
  )
}

import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchRingDetail, fetchRingExplanation } from '../api'
import { ArrowLeft, Users, Wifi, Smartphone, CreditCard, Brain, AlertTriangle } from 'lucide-react'
import ForceGraph2D from 'react-force-graph-2d'
import ReactMarkdown from 'react-markdown'

const NODE_COLORS = {
  customer: '#3b82f6',
  device: '#8b5cf6',
  ip: '#f59e0b',
  payment: '#10b981',
}

const NODE_SIZES = {
  customer: 6,
  device: 4,
  ip: 4,
  payment: 4,
}

export default function RingDetail() {
  const { ringId } = useParams()
  const [ring, setRing] = useState(null)
  const [explanation, setExplanation] = useState(null)
  const [loadingExplanation, setLoadingExplanation] = useState(false)
  const [loading, setLoading] = useState(true)
  const graphRef = useRef()

  useEffect(() => {
    fetchRingDetail(ringId).then(d => { setRing(d); setLoading(false) })
  }, [ringId])

  const handleExplain = () => {
    setLoadingExplanation(true)
    fetchRingExplanation(ringId).then(d => {
      setExplanation(d.explanation)
      setLoadingExplanation(false)
    }).catch(() => {
      setExplanation('⚠️ Failed to generate explanation. Check API connection.')
      setLoadingExplanation(false)
    })
  }

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const size = NODE_SIZES[node.type] || 4
    const color = NODE_COLORS[node.type] || '#64748b'

    // Glow effect
    ctx.shadowColor = color
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.fill()
    ctx.shadowBlur = 0

    // Label
    if (globalScale > 1.5) {
      ctx.font = `${Math.max(10 / globalScale, 2)}px Inter, sans-serif`
      ctx.fillStyle = '#e2e8f0'
      ctx.textAlign = 'center'
      ctx.fillText(node.label || node.id, node.x, node.y + size + 6 / globalScale)
    }
  }, [])

  if (loading) return <div><div className="spinner"></div><p className="loading-text">Loading ring data...</p></div>
  if (!ring) return <p>Ring not found.</p>

  const graphData = {
    nodes: (ring.graph?.nodes || []).map(n => ({...n, val: NODE_SIZES[n.type] || 4})),
    links: (ring.graph?.edges || []).map(e => ({
      source: e.source, target: e.target,
      color: e.type === 'device' ? 'rgba(139,92,246,0.3)' :
             e.type === 'ip' ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.3)'
    })),
  }

  return (
    <div className="fade-in">
      <Link to="/rings" className="back-link"><ArrowLeft size={16} /> Back to Ring Explorer</Link>

      {/* Header */}
      <div className="ring-detail-header">
        <div className="ring-icon">
          <AlertTriangle size={28} color="white" />
        </div>
        <div>
          <h2 style={{fontSize: 24}}>{ring.ring_id}</h2>
          <div style={{display: 'flex', gap: 8, marginTop: 8}}>
            <span className={`badge ${ring.ring_type}`}>{ring.ring_type}</span>
            <span className="badge critical">{ring.ring_size} members</span>
          </div>
        </div>
      </div>

      {/* Quick stats */}
      <div className="ring-detail-stats">
        <div className="mini-stat">
          <div className="value" style={{color: 'var(--accent-blue)'}}>{ring.ring_size}</div>
          <div className="label"><Users size={12} style={{marginRight: 4}} />Members</div>
        </div>
        <div className="mini-stat">
          <div className="value" style={{color: 'var(--accent-purple)'}}>{ring.num_shared_devices}</div>
          <div className="label"><Smartphone size={12} style={{marginRight: 4}} />Shared Devices</div>
        </div>
        <div className="mini-stat">
          <div className="value" style={{color: 'var(--accent-orange)'}}>{ring.num_shared_ips}</div>
          <div className="label"><Wifi size={12} style={{marginRight: 4}} />Shared IPs</div>
        </div>
        <div className="mini-stat">
          <div className="value" style={{color: 'var(--accent-green)'}}>{ring.num_shared_payments}</div>
          <div className="label"><CreditCard size={12} style={{marginRight: 4}} />Shared Payments</div>
        </div>
        <div className="mini-stat">
          <div className="value" style={{color: 'var(--accent-red)'}}>{(ring.avg_refund_rate * 100).toFixed(1)}%</div>
          <div className="label">Avg Refund Rate</div>
        </div>
        <div className="mini-stat">
          <div className="value" style={{color: 'var(--accent-cyan)'}}>₹{ring.total_amount?.toLocaleString()}</div>
          <div className="label">Total Amount</div>
        </div>
      </div>

      {/* Graph + LLM side by side */}
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24}}>
        {/* Graph visualization */}
        <div className="panel">
          <div className="panel-header">
            <h3>🕸️ Network Graph</h3>
            <div style={{display: 'flex', gap: 12, fontSize: 12}}>
              <span><span style={{color: NODE_COLORS.customer}}>●</span> Customer</span>
              <span><span style={{color: NODE_COLORS.device}}>●</span> Device</span>
              <span><span style={{color: NODE_COLORS.ip}}>●</span> IP</span>
              <span><span style={{color: NODE_COLORS.payment}}>●</span> Payment</span>
            </div>
          </div>
          <div className="graph-container">
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeCanvasObject={nodeCanvasObject}
              linkDirectionalParticles={1}
              linkDirectionalParticleSpeed={0.005}
              backgroundColor="#0a0e1a"
              width={520}
              height={420}
              cooldownTicks={100}
              onEngineStop={() => graphRef.current?.zoomToFit(400, 40)}
            />
          </div>
        </div>

        {/* LLM Explanation */}
        <div className="panel">
          <div className="panel-header">
            <h3><Brain size={18} style={{marginRight: 8, verticalAlign: 'middle'}} />AI Investigation Report</h3>
          </div>
          {!explanation && !loadingExplanation && (
            <div style={{textAlign: 'center', padding: '60px 20px'}}>
              <Brain size={48} color="var(--accent-purple)" style={{marginBottom: 16, opacity: 0.5}} />
              <p style={{color: 'var(--text-secondary)', marginBottom: 20}}>
                Generate an AI-powered investigation report for this ring
              </p>
              <button className="btn btn-primary" onClick={handleExplain}>
                <Brain size={16} /> Generate LLM Report
              </button>
            </div>
          )}
          {loadingExplanation && (
            <div style={{textAlign: 'center', padding: '60px 20px'}}>
              <div className="spinner"></div>
              <p className="loading-text">Groq (Llama 3) is analyzing this ring...</p>
            </div>
          )}
          {explanation && (
            <div className="llm-report">
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>

      {/* Members table */}
      <div className="panel">
        <div className="panel-header">
          <h3>👥 Ring Members ({ring.members?.length || 0})</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer ID</th>
              <th>Model Confidence</th>
              <th>Refund Rate</th>
              <th>Devices Used</th>
              <th>Shared Device Users</th>
              <th>Shared IP Users</th>
              <th>Transactions</th>
              <th>Avg Amount</th>
              <th>Account Age</th>
            </tr>
          </thead>
          <tbody>
            {(ring.members || []).map(m => (
              <tr key={m.customer_id}>
                <td style={{fontFamily: 'var(--font-mono)', fontSize: 13}}>{m.customer_id}</td>
                <td>
                  <span style={{
                    fontWeight: 700,
                    color: m.model_confidence > 0.9 ? '#ef4444' : m.model_confidence > 0.5 ? '#f59e0b' : '#10b981',
                    background: m.model_confidence > 0.9 ? 'rgba(239,68,68,0.1)' : 'transparent',
                    padding: '2px 8px', borderRadius: 4,
                  }}>
                    {(m.model_confidence * 100).toFixed(1)}%
                  </span>
                </td>
                <td style={{color: m.refund_rate > 0.2 ? 'var(--accent-red)' : 'var(--text-primary)'}}>
                  {(m.refund_rate * 100).toFixed(1)}%
                </td>
                <td>{m.num_devices_used}</td>
                <td>{m.shared_device_users}</td>
                <td>{m.shared_ip_users}</td>
                <td>{m.total_transactions}</td>
                <td>₹{m.avg_transaction_amount?.toLocaleString()}</td>
                <td>{m.account_age_days} days</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

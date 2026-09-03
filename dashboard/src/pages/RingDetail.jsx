import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchRingDetail, chatWithRing } from '../api'
import { ArrowLeft, Users, Wifi, Smartphone, CreditCard, Brain, AlertTriangle, Send, ShieldAlert, Shield, ShieldCheck, Key } from 'lucide-react'
import ForceGraph2D from 'react-force-graph-2d'
import ReactMarkdown from 'react-markdown'

function PolicyBadge({ action }) {
  if (action === 'HARD_BLOCK') {
    return (
      <div style={{display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: 6, color: '#ef4444', fontSize: 11, fontWeight: 700, letterSpacing: 0.5}}>
        <ShieldAlert size={14} /> HARD BLOCK
      </div>
    )
  }
  if (action === 'REVIEW') {
    return (
      <div style={{display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.4)', borderRadius: 6, color: '#f59e0b', fontSize: 11, fontWeight: 700, letterSpacing: 0.5}}>
        <Shield size={14} /> REVIEW
      </div>
    )
  }
  if (action === 'STEP_UP_AUTH') {
    return (
      <div style={{display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.4)', borderRadius: 6, color: '#3b82f6', fontSize: 11, fontWeight: 700, letterSpacing: 0.5}}>
        <Key size={14} /> CHALLENGE
      </div>
    )
  }
  return (
    <div style={{display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 10px', background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.4)', borderRadius: 6, color: '#10b981', fontSize: 11, fontWeight: 700, letterSpacing: 0.5}}>
      <ShieldCheck size={14} /> ALLOW
    </div>
  )
}

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

// Quick-suggestion buttons for the chat
const SUGGESTED_QUESTIONS = [
  "Who is the ringleader?",
  "Estimate the financial loss",
  "What action should we take?",
  "Explain the graph connections",
]

export default function RingDetail() {
  const { ringId } = useParams()
  const [ring, setRing] = useState(null)

  // Chat state
  const [chatHistory, setChatHistory] = useState([])
  const [chatInput, setChatInput] = useState('')
  const chatEndRef = useRef(null)

  const [loadingChat, setLoadingChat] = useState(false)
  const [loading, setLoading] = useState(true)
  const graphRef = useRef()

  useEffect(() => {
    fetchRingDetail(ringId).then(d => { setRing(d); setLoading(false) })
  }, [ringId])

  // Scroll to bottom of chat when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, loadingChat])

  const handleChat = async (message) => {
    if (!message.trim()) return

    const newHistory = [...chatHistory, { role: 'user', content: message }]
    setChatHistory(newHistory)
    setChatInput('')
    setLoadingChat(true)

    try {
      const res = await chatWithRing(ringId, message, chatHistory)
      setChatHistory([...newHistory, { role: 'assistant', content: res.reply || 'No response.' }])
    } catch (err) {
      setChatHistory([...newHistory, { role: 'assistant', content: 'Failed to connect to AI. Check backend.' }])
    }
    setLoadingChat(false)
  }

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const size = NODE_SIZES[node.type] || 4
    const color = NODE_COLORS[node.type] || '#64748b'

    ctx.shadowColor = color
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.fill()
    ctx.shadowBlur = 0

    if (globalScale > 1.5) {
      ctx.font = `${Math.max(10 / globalScale, 2)}px Inter, sans-serif`
      ctx.fillStyle = '#e2e8f0'
      ctx.textAlign = 'center'
      ctx.fillText(node.label || node.id, node.x, node.y + size + 6 / globalScale)
    }
  }, [])

  // MEMOIZE graph data so ForceGraph doesn't reset on every re-render
  const graphData = useMemo(() => {
    if (!ring?.graph) return { nodes: [], links: [] }
    return {
      nodes: (ring.graph.nodes || []).map(n => ({...n, val: NODE_SIZES[n.type] || 4})),
      links: (ring.graph.edges || []).map(e => ({
        source: e.source, target: e.target,
        color: e.type === 'device' ? 'rgba(139,92,246,0.3)' :
               e.type === 'ip' ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.3)'
      })),
    }
  }, [ring])

  if (loading) return <div><div className="spinner"></div><p className="loading-text">Loading ring data...</p></div>
  if (!ring) return <p>Ring not found.</p>

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
          <div className="value" style={{color: 'var(--accent-cyan)'}}>&#8377;{ring.total_amount?.toLocaleString()}</div>
          <div className="label">Total Amount</div>
        </div>
      </div>

      {/* Graph + Chat side by side */}
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24}}>
        {/* Graph visualization */}
        <div className="panel">
          <div className="panel-header">
            <h3>Network Graph</h3>
            <div style={{display: 'flex', gap: 12, fontSize: 12}}>
              <span><span style={{color: NODE_COLORS.customer}}>&#9679;</span> Customer</span>
              <span><span style={{color: NODE_COLORS.device}}>&#9679;</span> Device</span>
              <span><span style={{color: NODE_COLORS.ip}}>&#9679;</span> IP</span>
              <span><span style={{color: NODE_COLORS.payment}}>&#9679;</span> Payment</span>
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

        {/* AI Chat Interface */}
        <div className="panel" style={{display: 'flex', flexDirection: 'column', maxHeight: 530}}>
          <div className="panel-header" style={{marginBottom: 0, paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.05)', flexShrink: 0}}>
            <h3><Brain size={18} style={{marginRight: 8, verticalAlign: 'middle', color: 'var(--accent-purple)'}} />AI Investigation Assistant</h3>
            <span style={{fontSize: 11, color: 'var(--text-muted)', background: 'rgba(139,92,246,0.1)', padding: '3px 8px', borderRadius: 12}}>Groq LLM</span>
          </div>

          {/* Chat messages */}
          <div style={{flex: 1, overflowY: 'auto', padding: '12px 0', minHeight: 0}}>
            {chatHistory.length === 0 && !loadingChat && (
              <div style={{textAlign: 'center', padding: '30px 20px'}}>
                <Brain size={40} color="var(--accent-purple)" style={{marginBottom: 12, opacity: 0.4}} />
                <p style={{color: 'var(--text-secondary)', marginBottom: 16, fontSize: 14}}>
                  Ask the AI to investigate this ring
                </p>
                <button className="btn btn-primary" onClick={() => handleChat("Write a detailed investigation report for this ring, including risk score, key evidence, and recommended action.")} style={{marginBottom: 16}}>
                  <Brain size={16} /> Generate Report
                </button>
                <div style={{display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center'}}>
                  {SUGGESTED_QUESTIONS.map((q, i) => (
                    <button key={i} className="btn btn-outline" style={{padding: '4px 10px', fontSize: 11, borderRadius: 16}} onClick={() => handleChat(q)}>{q}</button>
                  ))}
                </div>
              </div>
            )}

            {chatHistory.map((msg, i) => (
              <div key={i} style={{
                marginBottom: 12, display: 'flex',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                gap: 8, padding: '0 4px'
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  background: msg.role === 'user' ? 'var(--accent-blue)' : 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {msg.role === 'user' ? <Users size={14} color="white" /> : <Brain size={14} color="white" />}
                </div>
                <div style={{
                  background: msg.role === 'user' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0,0,0,0.25)',
                  border: `1px solid ${msg.role === 'user' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)'}`,
                  padding: '10px 14px', borderRadius: 12, maxWidth: '85%',
                  borderTopRightRadius: msg.role === 'user' ? 4 : 12,
                  borderTopLeftRadius: msg.role === 'user' ? 12 : 4,
                }}>
                  {msg.role === 'user' ? (
                    <p style={{margin: 0, fontSize: 13}}>{msg.content}</p>
                  ) : (
                    <div className="llm-report" style={{fontSize: 13}}><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                  )}
                </div>
              </div>
            ))}

            {loadingChat && (
              <div style={{display: 'flex', gap: 8, marginBottom: 12, padding: '0 4px'}}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                  <Brain size={14} color="white" />
                </div>
                <div style={{padding: '10px 14px', background: 'rgba(0,0,0,0.25)', borderRadius: 12, borderTopLeftRadius: 4, display: 'flex', alignItems: 'center', gap: 6}}>
                  <div className="typing-dot"></div>
                  <div className="typing-dot" style={{animationDelay: '0.2s'}}></div>
                  <div className="typing-dot" style={{animationDelay: '0.4s'}}></div>
                </div>
              </div>
            )}

            {/* After initial report, show suggestion chips */}
            {chatHistory.length > 0 && chatHistory[chatHistory.length - 1].role === 'assistant' && !loadingChat && (
              <div style={{display: 'flex', flexWrap: 'wrap', gap: 6, padding: '4px 40px', marginTop: 4}}>
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button key={i} className="btn btn-outline" style={{padding: '3px 8px', fontSize: 10, borderRadius: 12, opacity: 0.7}} onClick={() => handleChat(q)}>{q}</button>
                ))}
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Chat input */}
          <div style={{flexShrink: 0, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.05)'}}>
            <form onSubmit={(e) => { e.preventDefault(); if (chatInput.trim()) handleChat(chatInput); }} style={{display: 'flex', gap: 8}}>
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ask a follow-up question..."
                disabled={loadingChat}
                style={{
                  flex: 1, padding: '10px 16px', borderRadius: 24,
                  background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)',
                  color: '#fff', outline: 'none', fontSize: 13,
                }}
                onFocus={e => e.target.style.borderColor = 'var(--accent-purple)'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
              <button type="submit" className="btn btn-primary" disabled={!chatInput.trim() || loadingChat} style={{borderRadius: 24, padding: '10px 16px', minWidth: 44}}>
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Members table */}
      <div className="panel">
        <div className="panel-header">
          <h3>Ring Members ({ring.members?.length || 0})</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer ID</th>
              <th>Model Confidence</th>
              <th>Policy</th>
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
                <td>
                  <PolicyBadge action={m.action} />
                </td>
                <td style={{color: m.refund_rate > 0.2 ? 'var(--accent-red)' : 'var(--text-primary)'}}>
                  {(m.refund_rate * 100).toFixed(1)}%
                </td>
                <td>{m.num_devices_used}</td>
                <td>{m.shared_device_users}</td>
                <td>{m.shared_ip_users}</td>
                <td>{m.total_transactions}</td>
                <td>&#8377;{m.avg_transaction_amount?.toLocaleString()}</td>
                <td>{m.account_age_days} days</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { fetchOverview } from '../api'
import { Users, AlertTriangle, ShieldCheck, Activity, TrendingUp, DollarSign } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#64748b']

export default function Overview() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOverview().then(d => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <div><div className="spinner"></div><p className="loading-text">Loading dashboard...</p></div>

  const modelChartData = (data.models || []).map(m => ({
    name: m.model?.replace(/[^\w\s()]/g, '').trim() || 'Unknown',
    Precision: m.precision,
    Recall: m.recall,
    F1: m.f1,
  }))

  const ringTypeData = Object.entries(data.ring_types || {}).map(([type, count]) => ({
    name: type,
    value: count,
  }))

  const customerTypeData = Object.entries(data.customer_types || {}).map(([type, count]) => ({
    name: type,
    value: count,
  }))

  return (
    <div className="fade-in">
      <div className="page-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
        <div>
          <h2>🛡️ Command Center</h2>
          <p>Real-time overview of the Abuse Ring detection system</p>
        </div>
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: 8, padding: '6px 14px', fontSize: 12, color: '#fbbf24', fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: 6
        }}>
          <span style={{width: 8, height: 8, borderRadius: '50%', background: '#fbbf24', display: 'inline-block'}}></span>
          SYNTHETIC DEMO DATA
        </div>
      </div>

      {/* Net Protected Value — headline business metric */}
      {data.net_protected_value > 0 && (
        <div className="panel fade-in" style={{
          marginBottom: 24, padding: '20px 28px',
          background: 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(59,130,246,0.08))',
          border: '1px solid rgba(16,185,129,0.2)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <div>
            <div style={{fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1}}>Net Protected Value</div>
            <div style={{fontSize: 32, fontWeight: 800, color: '#10b981'}}>
              ₹{data.net_protected_value?.toLocaleString('en-IN')}
            </div>
            <div style={{fontSize: 12, color: 'var(--text-muted)', marginTop: 4}}>
              Fraud prevented: ₹{data.fraud_value_protected?.toLocaleString('en-IN')} — FP friction cost: ₹{data.fp_cost?.toLocaleString('en-IN')}
            </div>
          </div>
          <DollarSign size={48} color="rgba(16,185,129,0.3)" />
        </div>
      )}

      {/* Stats cards */}
      <div className="stats-grid">
        <div className="stat-card fade-in fade-in-delay-1">
          <div className="stat-icon blue"><Users size={22} /></div>
          <div className="stat-value">{data.total_customers?.toLocaleString()}</div>
          <div className="stat-label">Total Customers</div>
        </div>
        <div className="stat-card fade-in fade-in-delay-2">
          <div className="stat-icon red"><AlertTriangle size={22} /></div>
          <div className="stat-value">{data.ring_members}</div>
          <div className="stat-label">Ring Members Detected</div>
        </div>
        <div className="stat-card fade-in fade-in-delay-3">
          <div className="stat-icon green"><ShieldCheck size={22} /></div>
          <div className="stat-value">{data.safe_users?.toLocaleString()}</div>
          <div className="stat-label">Safe Users</div>
        </div>
        <div className="stat-card fade-in fade-in-delay-4">
          <div className="stat-icon orange"><Activity size={22} /></div>
          <div className="stat-value">{data.total_rings}</div>
          <div className="stat-label">Abuse Rings</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="chart-grid">
        {/* Model Comparison */}
        <div className="panel fade-in fade-in-delay-2">
          <div className="panel-header">
            <h3><TrendingUp size={18} style={{marginRight: 8, verticalAlign: 'middle'}} />Model Performance</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelChartData} margin={{top: 5, right: 20, bottom: 60, left: 0}}>
              <XAxis dataKey="name" tick={{fill: '#94a3b8', fontSize: 11}} angle={-25} textAnchor="end" interval={0} />
              <YAxis tick={{fill: '#94a3b8', fontSize: 12}} domain={[0, 1]} />
              <Tooltip
                contentStyle={{background: '#1a1f35', border: '1px solid #1e293b', borderRadius: 8, color: '#e2e8f0'}}
              />
              <Bar dataKey="Precision" fill="#3b82f6" radius={[4,4,0,0]} />
              <Bar dataKey="Recall" fill="#10b981" radius={[4,4,0,0]} />
              <Bar dataKey="F1" fill="#f59e0b" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Ring Types Pie */}
        <div className="panel fade-in fade-in-delay-3">
          <div className="panel-header">
            <h3><AlertTriangle size={18} style={{marginRight: 8, verticalAlign: 'middle'}} />Ring Types Distribution</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={ringTypeData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name, value}) => `${name}: ${value}`}>
                {ringTypeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{background: '#1a1f35', border: '1px solid #1e293b', borderRadius: 8, color: '#e2e8f0'}} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model comparison table */}
      <div className="panel fade-in fade-in-delay-4">
        <div className="panel-header">
          <h3><DollarSign size={18} style={{marginRight: 8, verticalAlign: 'middle'}} />Model Comparison (Test Set)</h3>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Precision</th>
              <th>Recall</th>
              <th>F1 Score</th>
              <th>False Positives</th>
              <th>FP Cost (₹)</th>
            </tr>
          </thead>
          <tbody>
            {(data.models || []).map((m, i) => (
              <tr key={i}>
                <td style={{fontWeight: 600}}>{m.model}</td>
                <td><span style={{color: m.precision > 0.9 ? '#10b981' : '#f59e0b'}}>{(m.precision * 100).toFixed(1)}%</span></td>
                <td><span style={{color: m.recall > 0.9 ? '#10b981' : '#f59e0b'}}>{(m.recall * 100).toFixed(1)}%</span></td>
                <td><span style={{fontWeight: 700, color: m.f1 > 0.9 ? '#10b981' : m.f1 > 0.7 ? '#f59e0b' : '#ef4444'}}>{(m.f1 * 100).toFixed(1)}%</span></td>
                <td>{m.false_positives}</td>
                <td>₹{m.fp_cost_inr?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

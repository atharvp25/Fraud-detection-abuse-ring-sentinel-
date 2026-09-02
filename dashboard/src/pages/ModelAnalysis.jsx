import { useState, useEffect } from 'react'
import { fetchModels } from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import { TrendingUp, Award, Target } from 'lucide-react'

export default function ModelAnalysis() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchModels().then(d => { setData(d); setLoading(false) })
  }, [])

  if (loading) return <div><div className="spinner"></div><p className="loading-text">Loading model data...</p></div>

  const models = data?.models || []
  const featureImportance = data?.feature_importance || []

  // Find best model by F1
  const bestModel = models.reduce((best, m) => m.f1 > (best?.f1 || 0) ? m : best, null)

  const radarData = models.map(m => ({
    model: m.model?.replace(/[^\w\s()]/g, '').trim()?.substring(0, 15) || 'Unknown',
    Precision: m.precision,
    Recall: m.recall,
    F1: m.f1,
  }))

  return (
    <div className="fade-in">
      <div className="page-header">
        <h2>📊 Model Analysis</h2>
        <p>Performance comparison across 5 models — honest metrics including false-positive cost</p>
      </div>

      {/* Best model highlight */}
      {bestModel && (
        <div className="panel fade-in fade-in-delay-1" style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%)',
          borderColor: 'rgba(16, 185, 129, 0.3)',
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <Award size={32} color="var(--accent-green)" />
            <div>
              <h3 style={{color: 'var(--accent-green)'}}>Best Model: {bestModel.model}</h3>
              <p style={{color: 'var(--text-secondary)', fontSize: 14, marginTop: 4}}>
                F1: {(bestModel.f1 * 100).toFixed(1)}% | Precision: {(bestModel.precision * 100).toFixed(1)}% | 
                Recall: {(bestModel.recall * 100).toFixed(1)}% | FP Cost: ₹{bestModel.fp_cost_inr?.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Model comparison */}
      <div className="chart-grid" style={{marginTop: 24}}>
        {/* Detailed comparison table */}
        <div className="panel fade-in fade-in-delay-2">
          <div className="panel-header">
            <h3><Target size={18} style={{marginRight: 8, verticalAlign: 'middle'}} />Detailed Comparison</h3>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1</th>
                <th>FP</th>
                <th>FP Cost</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m, i) => (
                <tr key={i} style={{background: m === bestModel ? 'rgba(16, 185, 129, 0.05)' : 'transparent'}}>
                  <td style={{fontWeight: 600, fontSize: 13}}>{m.model}</td>
                  <td>
                    <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                      <div style={{width: 50, height: 4, background: 'var(--bg-primary)', borderRadius: 2, overflow: 'hidden'}}>
                        <div style={{width: `${m.precision * 100}%`, height: '100%', background: '#3b82f6', borderRadius: 2}}></div>
                      </div>
                      {(m.precision * 100).toFixed(1)}%
                    </div>
                  </td>
                  <td>
                    <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
                      <div style={{width: 50, height: 4, background: 'var(--bg-primary)', borderRadius: 2, overflow: 'hidden'}}>
                        <div style={{width: `${m.recall * 100}%`, height: '100%', background: '#10b981', borderRadius: 2}}></div>
                      </div>
                      {(m.recall * 100).toFixed(1)}%
                    </div>
                  </td>
                  <td style={{fontWeight: 700, color: m.f1 > 0.9 ? '#10b981' : m.f1 > 0.7 ? '#f59e0b' : '#ef4444'}}>
                    {(m.f1 * 100).toFixed(1)}%
                  </td>
                  <td>{m.false_positives}</td>
                  <td>₹{m.fp_cost_inr?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Radar chart */}
        <div className="panel fade-in fade-in-delay-3">
          <div className="panel-header">
            <h3><TrendingUp size={18} style={{marginRight: 8, verticalAlign: 'middle'}} />Model Radar</h3>
          </div>
          <ResponsiveContainer width="100%" height={350}>
            <RadarChart data={[
              {metric: 'Precision', ...Object.fromEntries(radarData.map(r => [r.model, r.Precision]))},
              {metric: 'Recall', ...Object.fromEntries(radarData.map(r => [r.model, r.Recall]))},
              {metric: 'F1', ...Object.fromEntries(radarData.map(r => [r.model, r.F1]))},
            ]}>
              <PolarGrid stroke="#1e293b" />
              <PolarAngleAxis dataKey="metric" tick={{fill: '#94a3b8', fontSize: 12}} />
              <PolarRadiusAxis domain={[0, 1]} tick={{fill: '#64748b', fontSize: 10}} />
              {radarData.map((r, i) => (
                <Radar key={r.model} name={r.model} dataKey={r.model}
                  stroke={['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'][i % 5]}
                  fill={['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'][i % 5]}
                  fillOpacity={0.1} strokeWidth={2} />
              ))}
              <Tooltip contentStyle={{background: '#1a1f35', border: '1px solid #1e293b', borderRadius: 8, color: '#e2e8f0'}} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Feature Importance */}
      <div className="panel fade-in fade-in-delay-4">
        <div className="panel-header">
          <h3>🔑 Feature Importance (XGBoost)</h3>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={featureImportance} layout="vertical" margin={{left: 160, right: 20}}>
            <XAxis type="number" tick={{fill: '#94a3b8', fontSize: 12}} domain={[0, 'auto']} />
            <YAxis type="category" dataKey="feature" tick={{fill: '#e2e8f0', fontSize: 12}} width={150} />
            <Tooltip contentStyle={{background: '#1a1f35', border: '1px solid #1e293b', borderRadius: 8, color: '#e2e8f0'}} />
            <Bar dataKey="importance" fill="#3b82f6" radius={[0,4,4,0]}
              background={{fill: 'rgba(30, 41, 59, 0.5)', radius: [0,4,4,0]}} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Methodology note */}
      <div className="panel" style={{borderColor: 'rgba(6, 182, 212, 0.3)', marginTop: 8}}>
        <h3 style={{color: 'var(--accent-cyan)', marginBottom: 12}}>📝 Evaluation Methodology</h3>
        <ul style={{color: 'var(--text-secondary)', fontSize: 14, lineHeight: 2, paddingLeft: 20}}>
          <li><strong>Grouped Split:</strong> All members of the same ring stay in the same split (train/val/test) — prevents data leakage</li>
          <li><strong>5 Models:</strong> Rules Baseline → XGBoost (Tabular) → XGBoost (Graph+ML) → Isolation Forest → Ensemble</li>
          <li><strong>FP Cost:</strong> Each wrongly blocked customer costs ₹60,000/year in lost revenue</li>
          <li><strong>Overfit Check:</strong> Train-Val F1 gap monitored — currently within acceptable range</li>
        </ul>
      </div>
    </div>
  )
}

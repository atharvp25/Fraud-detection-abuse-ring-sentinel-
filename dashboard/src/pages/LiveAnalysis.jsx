import { useState } from 'react'
import { Upload, FileDown, CheckCircle2, AlertTriangle, ShieldAlert, Cpu } from 'lucide-react'
import { uploadAndAnalyze } from '../api'

export default function LiveAnalysis() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [step, setStep] = useState(0) // 0: upload, 1: extracting, 2: predicting, 3: done

  const handleFileDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleAnalyze = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResults(null)
    setStep(1)
    
    // Simulate pipeline steps for visual effect
    setTimeout(() => setStep(2), 1500)
    setTimeout(() => setStep(3), 3000)

    try {
      const data = await uploadAndAnalyze(file)
      setTimeout(() => {
        setResults(data)
        setLoading(false)
      }, 3500)
    } catch (err) {
      setError(err.message)
      setLoading(false)
      setStep(0)
    }
  }

  const generateSampleCsv = () => {
    // Generate a basic sample CSV that matches our feature matrix
    const header = "customer_id,refund_rate,num_devices_used,shared_device_users,avg_accounts_per_device,shared_ip_users,total_transactions,total_amount_spent,avg_transaction_amount,txn_timespan_days\n"
    
    // Mix of safe and bad users
    const rows = [
      "SAFE_001,0.05,1,1,1.0,1,12,5000,416.6,180",
      "SAFE_002,0.02,2,1,1.0,1,45,12000,266.6,300",
      "SAFE_003,0.0,1,1,1.0,1,5,1500,300.0,30",
      "BAD_001,0.85,5,8,3.5,6,120,45000,375.0,2",
      "BAD_002,0.92,4,8,3.5,6,95,38000,400.0,1",
      "BAD_003,0.78,5,8,3.5,6,105,42000,400.0,3",
      "BAD_004,0.65,3,4,2.0,5,80,25000,312.5,5",
      "BAD_005,0.71,4,4,2.0,5,92,29000,315.2,6"
    ].join("\n")

    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.setAttribute('href', url)
    a.setAttribute('download', 'sample_features.csv')
    a.click()
  }

  return (
    <div className="fade-in">
      <div style={{marginBottom: 40}}>
        <h2>Live Analysis</h2>
        <p style={{color: 'var(--text-secondary)'}}>Upload a feature matrix CSV to run real-time inference using the XGBoost model.</p>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24}}>
        
        {/* Upload Panel */}
        <div className="panel">
          <div className="panel-header">
            <h3><Upload size={18} style={{marginRight: 8, verticalAlign: 'middle'}} /> Data Input</h3>
          </div>
          
          <div 
            onDragOver={e => e.preventDefault()} 
            onDrop={handleFileDrop}
            style={{
              border: '2px dashed rgba(255,255,255,0.1)',
              borderRadius: 'var(--radius-lg)',
              padding: '40px 20px',
              textAlign: 'center',
              background: 'rgba(0,0,0,0.2)',
              cursor: 'pointer',
              marginBottom: 20
            }}
            onClick={() => document.getElementById('csv-upload').click()}
          >
            <input 
              id="csv-upload" 
              type="file" 
              accept=".csv" 
              style={{display: 'none'}} 
              onChange={handleFileSelect}
            />
            <Upload size={48} color={file ? 'var(--accent-green)' : 'var(--text-muted)'} style={{marginBottom: 16}} />
            <h4 style={{marginBottom: 8}}>{file ? file.name : "Drag & Drop CSV here"}</h4>
            <p style={{color: 'var(--text-secondary)', fontSize: 14}}>
              {file ? `${(file.size / 1024).toFixed(1)} KB` : "or click to browse"}
            </p>
          </div>

          <div style={{display: 'flex', gap: 12}}>
            <button className="btn btn-primary" style={{flex: 1}} onClick={handleAnalyze} disabled={!file || loading}>
              <Cpu size={16} /> {loading ? "Processing..." : "Run Analysis"}
            </button>
            <button className="btn btn-outline" onClick={generateSampleCsv} disabled={loading}>
              <FileDown size={16} /> Sample CSV
            </button>
          </div>
          {error && (
            <div style={{marginTop: 16, padding: 12, background: 'rgba(239,68,68,0.1)', color: '#fca5a5', borderRadius: 8, border: '1px solid rgba(239,68,68,0.3)', fontSize: 14}}>
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* Pipeline Animation / Status Panel */}
        <div className="panel" style={{display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'}}>
          {!loading && !results && (
            <div style={{textAlign: 'center', opacity: 0.5}}>
              <ShieldAlert size={64} style={{marginBottom: 16}} />
              <p>System Ready for Live Inference</p>
            </div>
          )}
          
          {loading && (
            <div style={{width: '100%', maxWidth: 300}}>
              <h3 style={{textAlign: 'center', marginBottom: 24, color: 'var(--accent-blue)'}}>Analyzing Data...</h3>
              
              <div style={{display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16}}>
                <div style={{width: 24, height: 24, borderRadius: '50%', background: step >= 1 ? 'var(--accent-green)' : 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                  {step >= 1 && <CheckCircle2 size={16} color="black" />}
                </div>
                <span style={{color: step >= 1 ? '#fff' : 'var(--text-muted)'}}>Extracting Features</span>
              </div>

              <div style={{display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16}}>
                <div style={{width: 24, height: 24, borderRadius: '50%', background: step >= 2 ? 'var(--accent-green)' : 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                  {step >= 2 && <CheckCircle2 size={16} color="black" />}
                </div>
                <span style={{color: step >= 2 ? '#fff' : 'var(--text-muted)'}}>XGBoost Prediction</span>
              </div>

              <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <div style={{width: 24, height: 24, borderRadius: '50%', background: step >= 3 ? 'var(--accent-green)' : 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                  {step >= 3 && <CheckCircle2 size={16} color="black" />}
                </div>
                <span style={{color: step >= 3 ? '#fff' : 'var(--text-muted)'}}>Risk Scoring & Clustering</span>
              </div>
            </div>
          )}

          {results && (
            <div style={{textAlign: 'center'}}>
              <div style={{
                width: 80, height: 80, borderRadius: '50%', margin: '0 auto 16px',
                background: results.flagged_count > 0 ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: `2px solid ${results.flagged_count > 0 ? 'var(--accent-red)' : 'var(--accent-green)'}`
              }}>
                {results.flagged_count > 0 ? <AlertTriangle size={40} color="var(--accent-red)" /> : <CheckCircle2 size={40} color="var(--accent-green)" />}
              </div>
              <h2 style={{marginBottom: 8}}>{results.flagged_count > 0 ? "Threat Detected" : "Clean"}</h2>
              <p style={{color: 'var(--text-secondary)'}}>
                Analyzed {results.total_analyzed} accounts. Found {results.flagged_count} suspicious members.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      {results && results.flagged_count > 0 && (
        <div className="panel fade-in" style={{marginTop: 24}}>
          <div className="panel-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <h3>🚨 Flagged Accounts</h3>
            <span className="badge critical">Avg Risk: {results.avg_risk}%</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>Risk Score</th>
                <th>Refund Rate</th>
                <th>Devices</th>
                <th>Amount</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {results.flagged_customers.map(c => (
                <tr key={c.customer_id}>
                  <td style={{fontFamily: 'var(--font-mono)'}}>{c.customer_id}</td>
                  <td>
                    <span style={{
                      fontWeight: 700,
                      color: c.risk_score > 90 ? '#ef4444' : c.risk_score > 50 ? '#f59e0b' : '#10b981',
                      background: c.risk_score > 90 ? 'rgba(239,68,68,0.1)' : 'transparent',
                      padding: '2px 8px', borderRadius: 4,
                    }}>
                      {c.risk_score}%
                    </span>
                  </td>
                  <td>{c.refund_rate}%</td>
                  <td>{c.devices}</td>
                  <td>₹{c.amount.toLocaleString()}</td>
                  <td><button className="btn btn-outline" style={{padding: '4px 12px', fontSize: 12}}>Freeze</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

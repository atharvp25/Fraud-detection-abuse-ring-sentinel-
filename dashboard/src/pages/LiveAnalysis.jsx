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
    // All 18 features the XGBoost model expects
    const header = "customer_id,account_age_days,total_transactions,total_refunds,refund_rate,avg_transaction_amount,max_transaction_amount,total_amount_spent,transaction_velocity,txn_timespan_days,num_devices_used,num_ips_used,num_payments_used,shared_device_users,shared_ip_users,shared_payment_users,avg_accounts_per_device,avg_accounts_per_ip,avg_accounts_per_payment\n"
    
    // Mix of safe and fraudulent users
    const rows = [
      // Safe users: low refund, few devices, long account age, normal velocity
      "SAFE_001,365,30,1,0.03,450,1200,13500,0.08,340,1,2,1,1,1,1,1.0,1.0,1.0",
      "SAFE_002,720,95,2,0.02,280,800,26600,0.13,650,2,2,2,1,1,1,1.0,1.2,1.0",
      "SAFE_003,180,12,0,0.0,600,2000,7200,0.07,160,1,1,1,1,1,1,1.0,1.0,1.0",
      "SAFE_004,540,45,3,0.07,320,950,14400,0.08,480,1,2,1,1,2,1,1.0,1.5,1.0",
      "SAFE_005,90,8,0,0.0,150,400,1200,0.09,75,1,1,1,1,1,1,1.0,1.0,1.0",
      // Fraudulent users: high refund, many shared devices, short timespan, high velocity
      "FRAUD_001,14,120,96,0.80,380,1500,45600,8.57,5,5,4,3,8,6,5,3.5,2.8,2.2",
      "FRAUD_002,7,95,87,0.92,410,1800,38950,13.57,3,4,3,3,8,6,5,3.5,2.8,2.2",
      "FRAUD_003,21,105,82,0.78,400,1600,42000,5.00,8,5,4,3,8,6,5,3.5,2.8,2.2",
      "FRAUD_004,10,80,52,0.65,310,1200,24800,8.00,4,3,3,2,4,5,3,2.0,2.0,1.8",
      "FRAUD_005,12,92,65,0.71,315,1400,28980,7.67,6,4,3,2,4,5,3,2.0,2.0,1.8"
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

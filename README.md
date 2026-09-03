# 🛡️ Abuse Ring Sentinel

**AI-powered fraud ring detection system for fintech ecosystems — built for the Razorpay Hackathon.**

Detects coordinated abuse rings (refund fraud, promo abuse, triangulation) using XGBoost ML, graph analysis, and LLM-powered investigation — with an actionable policy layer that maps risk scores to real business decisions.

---

## 🎯 Problem Statement

Individual fraud detection misses **coordinated attacks** — rings of accounts sharing devices, IPs, and payment methods to systematically exploit refund policies, promo codes, and payment systems. Abuse Ring Sentinel detects these hidden networks.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **ML Risk Scoring** | XGBoost model trained on 21 engineered features (F1: 0.996) |
| **Action Policy Layer** | Risk → `ALLOW` / `STEP_UP_AUTH` / `REVIEW` / `HARD_BLOCK` |
| **Net Protected Value** | Business-impact metric: Fraud Prevented − FP Friction Cost |
| **Network Graph Visualization** | Force-directed graphs showing device/IP/payment linkages |
| **AI Investigation Assistant** | LLM-powered chat that analyzes ring topology and identifies ringleaders |
| **Live CSV Analysis** | Upload customer features → instant real-time predictions |
| **7 Fraud Archetypes** | RaaS, Triangulation, Stealth, Promo Abuse, Device Farm, Synthetic ID, Mule Network |

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   React + Vite  │◄──►│  FastAPI Backend  │◄──►│  XGBoost + Groq LLM │
│   (Dashboard)   │    │  (REST API)      │    │  (ML + AI Engine)   │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

---

## 📂 Project Structure

```
abuse-ring-sentinel/
├── backend/                        # FastAPI Backend
│   ├── main.py                     # API endpoints, ML inference, action policy
│   └── llm_engine/                 # Groq LLM integration for AI chat
│       ├── __init__.py
│       └── explain.py
├── dashboard/                      # React Frontend (Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Overview.jsx        # Command Center + Net Protected Value
│   │   │   ├── RingExplorer.jsx    # Ring investigation queue + Policy badges
│   │   │   ├── RingDetail.jsx      # Graph visualization + AI chat
│   │   │   ├── LiveAnalysis.jsx    # CSV upload → real-time prediction
│   │   │   └── ModelAnalysis.jsx   # Model comparison dashboard
│   │   ├── App.jsx                 # Router + Sidebar layout
│   │   ├── api.js                  # API client
│   │   └── index.css               # Design system (dark theme)
│   └── package.json
├── ml/                             # Machine Learning
│   ├── pipeline/                   # Feature engineering + model training
│   │   ├── feature_engineering.py  # 21-feature extraction pipeline
│   │   ├── train_models.py         # XGBoost, Isolation Forest, Ensemble
│   │   ├── evaluate.py             # Precision, Recall, F1, FP cost
│   │   └── graph_features.py       # Network degree & clustering features
│   └── data_generator/             # Synthetic data generation (7 archetypes)
│       ├── run_generator.py        # Orchestrator
│       ├── config.py               # Ring type definitions
│       └── generate_*.py           # Customer, transaction, network generators
├── requirements.txt                # Python dependencies
├── .gitignore
└── README.md
```

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- Groq API Key ([get one free](https://console.groq.com))

### 1. Clone & Install
```bash
git clone https://github.com/atharvp25/Fraud-detection-abuse-ring-sentinel-.git
cd Fraud-detection-abuse-ring-sentinel-

# Python backend
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt

# React frontend
cd dashboard
npm install
cd ..
```

### 2. Configure Environment
```bash
# Create .env file in project root
echo GROQ_API_KEY=your_groq_api_key_here > .env
```

### 3. Generate Data & Train Model
```bash
python ml/data_generator/run_generator.py
python ml/pipeline/feature_engineering.py
python ml/pipeline/train_models.py
```

### 4. Run the Application
Open **two terminals**:

**Terminal 1 — Backend (port 8000)**
```bash
.\venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend (port 5173)**
```bash
cd dashboard
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 📊 Model Performance (Test Set)

| Model | Precision | Recall | F1 Score | False Positives | FP Cost (₹) |
|---|---|---|---|---|---|
| Rules Baseline | 94.7% | 27.5% | 42.6% | 2 | ₹1,20,000 |
| **XGBoost (Tabular)** | **99.2%** | **100%** | **99.6%** | **1** | **₹60,000** |
| XGBoost (Graph+ML) | 99.2% | 99.2% | 99.2% | 1 | ₹60,000 |
| Isolation Forest | 67.7% | 51.1% | 58.3% | 32 | ₹19,20,000 |
| Ensemble (XGB+IF) | 79.8% | 99.2% | 88.4% | 33 | ₹19,80,000 |

### Action Policy Mapping
| Risk Score | Policy | Action |
|---|---|---|
| < 90 | `ALLOW` | Transaction proceeds normally |
| 90–95 | `STEP_UP_AUTH` | Require OTP / additional verification |
| 96–98 | `REVIEW` | Send to manual fraud analyst queue |
| ≥ 99 | `HARD_BLOCK` | Immediately block the transaction |

---

## 🏆 Fraud Archetypes Detected

| Archetype | Description |
|---|---|
| **Refund-as-a-Service (RaaS)** | Organized rings sharing devices to abuse refund policies |
| **Triangulation Fraud** | Stolen cards laundered across multiple coordinated accounts |
| **Stealth Rings** | Long-running networks that mask connections over months |
| **Promo Abuse** | Burst accounts harvesting sign-up bonuses then vanishing |
| **Device Farms** | Many accounts operated from a small pool of shared devices |
| **Synthetic Identity** | Fabricated customer profiles with no real transaction history |
| **Mule Networks** | Money-laundering chains passing funds through intermediaries |

---

## ⚠️ Limitations

> **Synthetic benchmark performance ≠ production fraud performance.**

This system is trained on synthetic data with 7 realistic fraud archetypes, hard negatives, and Gaussian noise injection. The near-perfect metrics (F1=0.996) reflect the controlled environment. In production:
- Recall would likely be 85–95% due to unseen fraud patterns.
- Continuous retraining on real transaction data would be essential.
- Policy thresholds would require calibration with domain fraud experts.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Recharts, react-force-graph-2d, Lucide Icons |
| Backend | FastAPI, Uvicorn, Pandas, NumPy |
| ML | XGBoost, scikit-learn, NetworkX |
| AI | Groq Cloud (Qwen 2.5 LLM) |
| Data | Custom synthetic generator (10,380 customers, 66 rings) |

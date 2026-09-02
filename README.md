# Abuse Ring Sentinel 🛡️

A comprehensive, end-to-end Machine Learning system for detecting and investigating complex fraud rings, organized abuse, and coordinated attacks in fintech ecosystems.

## 🚀 Features

### 1. Advanced Machine Learning Pipeline
- **Hybrid Approach:** Combines Tabular XGBoost, Graph ML (Network properties), and Isolation Forests.
- **High Recall:** F1 Score of ~0.99 for catching coordinated abuse rings with low false positives.
- **Robust Feature Engineering:** Extracts time-velocity signals, shared device overlaps, and network degrees.

### 2. Live Analysis & CSV Prediction
- Upload custom feature matrices (CSV) directly to the dashboard.
- Watch real-time execution of XGBoost prediction.
- Instantly view flagged threat clusters and risk scores.

### 3. AI Investigation Assistant (Powered by Groq Llama 3)
- Multi-turn AI chat interface built directly into the Ring Explorer.
- The LLM acts as a Senior Fraud Analyst with full context of the Ring's graph connections, stats, and members.
- Auto-generates detailed, structured investigation reports on demand.

### 4. Interactive Dashboard
- **Glassmorphism UI:** Built with React & Vite, featuring a dark-mode premium UI.
- **Network Graphs:** Force-directed 2D graph visualizations of devices, IPs, and payments.
- **Model Analysis:** Detailed metrics and feature importance charts comparing model performance.

## 🏗️ Architecture

1. **Data Generation (`data_generator/`)**
   - Synthesizes realistic transactional data, devices, IPs, and complex fraud archetypes (RaaS, Stealth Rings, Device Farms).
2. **ML Pipeline (`ml_pipeline/`)**
   - `feature_engineering.py`: Processes raw logs into a robust feature matrix.
   - `train_models.py`: Trains and evaluates multiple models (XGBoost, Isolation Forest, Ensembles).
3. **Backend (`backend.py`)**
   - FastAPI server serving ML predictions, dataset analytics, and the Groq LLM integration.
4. **Frontend (`dashboard/`)**
   - React application for data visualization and live AI chat.

## 🛠️ Setup & Installation

### Requirements
- Python 3.9+
- Node.js 18+

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/abuse-ring-sentinel.git
cd abuse-ring-sentinel

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure Environment Variables
# Create a .env file and add your Groq API key
echo "GROQ_API_KEY=your_api_key_here" > .env
# Optional: Set your preferred Groq model
echo "GROQ_MODEL=llama3-8b-8192" >> .env
```

### 2. Run Data Pipeline (Optional, pre-trained model included)
```bash
# Generate synthetic data, engineer features, and train the models
python data_generator/run_generator.py
python ml_pipeline/feature_engineering.py
python ml_pipeline/train_models.py
```

### 3. Start the Application
You need two terminal windows.

**Terminal 1: FastAPI Backend**
```bash
.\venv\Scripts\activate
uvicorn backend:app --reload --port 8000
```

**Terminal 2: React Dashboard**
```bash
cd dashboard
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## 📂 Project Structure

```text
abuse_ring_sentinel/
├── backend.py                  # FastAPI Backend Server
├── dashboard/                  # React Frontend
├── data_generator/             # Synthetic Data Generation
├── llm_engine/                 # Groq AI Investigation Module
├── ml_pipeline/                # Feature Engineering & Model Training
├── models/                     # Saved XGBoost Models
├── data/                       # Raw & Processed Datasets
└── README.md                   
```

## 🏆 Use Cases & Fraud Archetypes Handled
- **Refund as a Service (RaaS):** Highly connected rings sharing devices to abuse refund policies.
- **Triangulation Fraud:** Rings using stolen cards across multiple accounts.
- **Stealth Rings:** Coordinated networks masking their connections over long time periods.
- **Promo Abuse:** Temporary, fast-burning accounts created to harvest sign-up bonuses.

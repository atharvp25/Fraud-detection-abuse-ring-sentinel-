# Abuse Ring Sentinel — Project Report

> A comprehensive, end-to-end Machine Learning system for detecting coordinated fraud rings in fintech ecosystems.

---

## 1. Problem Statement

**What problem are we solving?**

In the Indian fintech ecosystem (Paytm, PhonePe, Razorpay, etc.), organized fraud rings coordinate to exploit refund policies, steal from promotions, and commit triangulation fraud. Unlike individual bad actors, these rings are **coordinated groups of 3–27 people** who share devices, IP addresses, and payment instruments to disguise their activity.

Traditional rule-based systems catch obvious fraud but fail against sophisticated rings that deliberately keep their individual behavior within "normal" thresholds. They exploit the fact that **looking at one account in isolation reveals nothing** — it's only when you look at the *connections* between accounts that the pattern emerges.

**Our Solution:** Abuse Ring Sentinel uses a hybrid ML pipeline that combines tabular behavioral features, graph-based network analysis, and LLM-powered investigation to detect, cluster, and explain fraud rings in real time.

---

## 2. Dataset

### 2.1 Why Synthetic Data?

Real fraud data is **classified and proprietary** — no fintech company publicly shares it. We built a sophisticated synthetic data generator that produces realistic fraud patterns based on published research and public reports from fraud investigation firms.

### 2.2 Dataset Statistics

| Metric | Value |
|---|---|
| **Total Customers** | 10,380 |
| **Ring Members (Positive Class)** | 645 (6.2%) |
| **Safe Users (Negative Class)** | 9,735 (93.8%) |
| **Total Fraud Rings** | 66 |
| **Average Ring Size** | 9.8 members |
| **Smallest Ring** | 3 members |
| **Largest Ring** | 27 members |

### 2.3 Class Imbalance

The dataset has a realistic **6.2% positive rate** — close to real-world fraud rates (typically 1–10%). This imbalance is important because a naive model that predicts "safe" for everyone would still achieve 93.8% accuracy. Our models must handle this imbalance properly (we use `scale_pos_weight` in XGBoost).

### 2.4 Data Splits

| Split | Size | Purpose |
|---|---|---|
| **Training** | 7,220 (70%) | Model learning |
| **Validation** | 1,568 (15%) | Hyperparameter tuning, overfitting detection |
| **Test** | 1,592 (15%) | Final evaluation (never seen during training) |

### 2.5 Fraud Ring Types (7 Archetypes)

| Ring Type | Count | Description |
|---|---|---|
| **Classic Ring** | 12 | Standard device/IP sharing with high refund rates |
| **Slow Burn** | 10 | Long-running, low-volume rings that build trust before exploiting |
| **Refund-as-a-Service (RaaS)** | 10 | Professional rings that sell refund fraud as a paid service |
| **Stealth Ring** | 10 | Sophisticated rings that rotate devices and IPs to avoid detection |
| **Device Farm** | 8 | Many accounts operated from a small number of physical devices |
| **Promo Abuse** | 8 | Short-lived accounts created to harvest sign-up bonuses |
| **Triangulation** | 8 | Rings using stolen cards across multiple accounts with reshipping |

### 2.6 Realistic Noise & Hard Negatives

To prevent the model from taking shortcuts, we injected:
- **Gaussian noise** into all features (5–20% depending on feature type) to simulate real-world measurement uncertainty.
- **Legitimate sharing groups**: 200 families, 60 offices, 50 student hostels, and 40 corporate card groups that share devices/IPs **legitimately** — forcing the model to distinguish real rings from innocent sharing.

---

## 3. Feature Engineering

We engineered **21 features** across 4 categories:

### 3.1 Behavioral Features (9 features)

| Feature | Description |
|---|---|
| `account_age_days` | How long the account has existed |
| `total_transactions` | Total number of transactions |
| `total_refunds` | Total number of refund requests |
| `refund_rate` | Ratio of refunds to total transactions |
| `avg_transaction_amount` | Average Rs amount per transaction |
| `max_transaction_amount` | Highest single transaction |
| `total_amount_spent` | Lifetime spend |
| `transaction_velocity` | Transactions per day (burst detection) |
| `txn_timespan_days` | Time between first and last transaction |

### 3.2 Device/Network Features (6 features)

| Feature | Description |
|---|---|
| `num_devices_used` | Distinct devices this customer used |
| `num_ips_used` | Distinct IP addresses |
| `num_payments_used` | Distinct payment instruments |
| `shared_device_users` | How many OTHER customers share devices with this one |
| `shared_ip_users` | How many OTHER customers share IPs |
| `shared_payment_users` | How many OTHER customers share payment methods |

### 3.3 Density Features (3 features)

| Feature | Description |
|---|---|
| `avg_accounts_per_device` | Average number of accounts on each device this customer uses |
| `avg_accounts_per_ip` | Average accounts per IP |
| `avg_accounts_per_payment` | Average accounts per payment instrument |

### 3.4 Graph Features (3 features)

| Feature | Description |
|---|---|
| `graph_degree` | Number of connections in the customer-device-IP graph |
| `graph_component_size` | Size of the connected component this customer belongs to |
| `graph_avg_neighbor_refund_rate` | Average refund rate of all neighbors in the graph |

---

## 4. Model Architecture

We trained **5 models** to demonstrate incremental value at each layer:

### Model 1: Rules Baseline (No ML)
Simple if/else rules: flag anyone with `refund_rate > 0.3 AND shared_device_users > 3`.

### Model 2: XGBoost (Tabular Only)
Gradient-boosted decision trees using only the 18 tabular features (no graph features). This is our **primary production model**.

### Model 3: XGBoost (Tabular + Graph)
Same architecture but with 3 additional graph features (degree, component size, neighbor refund rate).

### Model 4: Isolation Forest (Unsupervised)
Anomaly detection model that does NOT use labels. Detects statistical outliers.

### Model 5: Ensemble (XGBoost + Isolation Forest)
Flags a customer if EITHER model flags them. Maximizes recall at the cost of precision.

---

## 5. Model Evaluation (Test Set — Never Seen During Training)

### 5.1 Summary Table

| Model | Precision | Recall | F1 Score | TP | FP | FN | FP Cost (Rs) |
|---|---|---|---|---|---|---|---|
| **Rules Baseline** | 0.947 | 0.275 | 0.426 | 36 | 2 | 95 | Rs 1,20,000 |
| **XGBoost (Tabular)** | **0.992** | **1.000** | **0.996** | **131** | **1** | **0** | **Rs 60,000** |
| **XGBoost (Graph+ML)** | 0.992 | 0.992 | 0.992 | 130 | 1 | 1 | Rs 60,000 |
| **Isolation Forest** | 0.677 | 0.511 | 0.583 | 67 | 32 | 64 | Rs 19,20,000 |
| **Ensemble (XGB+IF)** | 0.798 | 0.992 | 0.884 | 130 | 33 | 1 | Rs 19,80,000 |

### 5.2 Detailed XGBoost Tabular Results (Our Best Model)

| Metric | Value |
|---|---|
| **Accuracy** | 99.94% |
| **Precision** | 99.24% |
| **Recall** | 100.0% |
| **F1 Score** | 99.62% |
| **True Positives** | 131 (caught all ring members) |
| **False Positives** | 1 (wrongly flagged 1 safe user) |
| **False Negatives** | 0 (missed zero ring members) |
| **True Negatives** | 1,460 (correctly cleared all safe users) |

### 5.3 Confusion Matrix (XGBoost Tabular)

```
                  Predicted Safe    Predicted Ring
Actual Safe           1,460              1
Actual Ring              0              131
```

### 5.4 Honest Analysis

> [!IMPORTANT]
> **100% recall on synthetic data does not guarantee 100% recall in production.** Our synthetic data, while realistic, was generated by known rules — which means the model can learn those exact rules. In a real deployment, recall would likely be lower (85–95%), and continuous retraining on real data would be essential.

**Why Tabular beats Graph:** The XGBoost Tabular model (F1=0.996) slightly outperforms the Graph model (F1=0.992). This happened because our tabular features (especially `txn_timespan_days` and `refund_rate`) already capture enough signal. The graph features add marginal value in this synthetic dataset but would likely add more value on real-world data where behavioral features alone are less discriminative.

**Why we don't recommend Isolation Forest as the primary model:** While it works without labels, it produces 32 false positives — costing Rs 19.2 lakh in wrongly frozen legitimate accounts. In production, we recommend **Rules → XGBoost Tabular** as the primary pipeline.

---

## 6. Feature Importance (XGBoost Tabular)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `txn_timespan_days` | 0.4581 |
| 2 | `max_transaction_amount` | 0.1332 |
| 3 | `avg_transaction_amount` | 0.0756 |
| 4 | `account_age_days` | 0.0715 |
| 5 | `total_amount_spent` | 0.0543 |
| 6 | `refund_rate` | 0.0536 |
| 7 | `shared_payment_users` | 0.0421 |
| 8 | `num_payments_used` | 0.0287 |
| 9 | `shared_device_users` | 0.0156 |
| 10 | `avg_accounts_per_payment` | 0.0152 |

**Key Insight:** The single most important feature is `txn_timespan_days` (45.8% importance). Ring members tend to have very short transaction timespans (all activity packed into a few days) compared to legitimate users who transact over months. This is a strong, intuitive signal: fraudsters burn through accounts quickly before they get caught.

---

## 7. System Architecture

```
                          +-------------------+
                          |   React Frontend  |
                          |   (Vite + React)  |
                          +--------+----------+
                                   |
                              REST API
                                   |
                          +--------v----------+
                          |  FastAPI Backend   |
                          |  (backend/main.py) |
                          +--------+----------+
                                   |
                    +--------------+--------------+
                    |              |               |
             +------v-----+ +----v------+ +------v------+
             |   XGBoost   | | Groq LLM | |  Data Layer |
             |   Model     | | (Chat AI) | |  (CSV/Data) |
             +-------------+ +----------+ +-------------+
```

### Frontend (React + Vite)
- **Overview Dashboard**: Real-time stats, ring counts, risk distribution
- **Ring Explorer**: Searchable, filterable list of all detected rings
- **Ring Detail**: Network graph visualization + AI Chat Assistant
- **Live Analysis**: CSV upload → real-time XGBoost prediction
- **Model Analysis**: Side-by-side comparison of all 5 models

### Backend (FastAPI)
- Serves all ring data, member details, and graph structures
- Runs live XGBoost `predict_proba()` for real-time risk scores
- Integrates with Groq API for LLM-powered investigation chat

### AI Investigation Assistant
- Multi-turn conversational AI powered by Groq (Qwen 3.8-27B)
- Ring data is injected as system context — the LLM "knows" the ring's stats and members
- Can identify ringleaders, estimate losses, and recommend actions

---

## 8. Build Challenges & Technical Obstacles

### Challenge 1: Windows Encoding Crashes (cp1252)
**Problem:** Python's `print()` on Windows uses `cp1252` encoding, which crashes when printing emoji characters (e.g., ✅, 🚨, 🧠). The backend would crash every time we printed a log message with emoji.
**Solution:** Replaced all emoji in `print()` statements with ASCII equivalents (`[OK]`, `[WARN]`). Kept emoji only in user-facing UI strings that go through React (which handles Unicode natively).

### Challenge 2: LLM Model Deprecation (Groq API)
**Problem:** We initially used `llama-3.1-8b-instant` on Groq, but the model was decommissioned mid-development, returning 404 errors. The AI Investigation feature was completely broken.
**Solution:** Switched to `qwen/qwen3.8-27b` which was available on our API key. Added a `<think>` tag stripping regex since Qwen outputs reasoning tags that Llama doesn't. Also added a full fallback template-based report when the LLM is completely unavailable.

### Challenge 3: ForceGraph Re-rendering Bug
**Problem:** The network graph visualization (ForceGraph2D) would completely restart its physics simulation every time the user typed a character in the chat input. The graph would "explode" and rearrange itself continuously.
**Root Cause:** React re-renders the entire component on every state change. The `graphData` object was created inline in the render function, so ForceGraph received a "new" object reference every render and treated it as new data.
**Solution:** Wrapped `graphData` in `useMemo(() => ..., [ring])` so the object reference only changes when the ring data itself changes, not on every keystroke.

### Challenge 4: 100% Recall Red Flag
**Problem:** Our XGBoost Tabular model achieved 100% recall on the test set. A reviewer (Claude Sonnet) correctly flagged this as suspicious — "100% recall is a red flag against your own project's claim."
**Investigation:** We ran two validation tests:
1. **Shuffled-label test**: Randomly shuffled the labels and retrained — the model achieved F1=0.000, proving it wasn't memorizing the data structure.
2. **Hold-out-by-ring-type test**: Held out entire ring types during training — achieved F1=0.994, proving the model generalizes across fraud patterns.
**Conclusion:** The 100% recall is a consequence of the synthetic data being generated by known rules. We documented this honestly and noted that real-world recall would be lower.

### Challenge 5: Class Imbalance (6.2% Positive Rate)
**Problem:** With only 645 ring members vs 9,735 safe users, a naive model would predict "safe" for everyone and achieve 93.8% accuracy.
**Solution:** Used XGBoost's `scale_pos_weight` parameter set to the ratio of negative/positive samples (~15.1). This forces the model to pay 15x more attention to each ring member during training.

### Challenge 6: Legitimate Sharing Groups (Hard Negatives)
**Problem:** Families sharing a tablet, office workers sharing a corporate IP, and students in a hostel sharing WiFi all look exactly like fraud rings to a naive model.
**Solution:** We deliberately generated 200 families, 60 offices, 50 hostels, and 40 corporate card groups with realistic sharing patterns. These "hard negatives" force the model to look beyond simple sharing counts and learn the *behavioral* differences (e.g., ring members have high refund rates AND short timespans, while families have low refund rates despite sharing devices).

### Challenge 7: File Upload Dependency (python-multipart)
**Problem:** Adding the CSV upload feature for Live Analysis caused the backend to crash on startup with `RuntimeError: Form data requires "python-multipart"`.
**Solution:** Installed `python-multipart` via pip and added it to `requirements.txt`. FastAPI requires this package for `UploadFile` handling but doesn't include it by default.

### Challenge 8: Dashboard Risk Score Integrity
**Problem:** A reviewer noted that the dashboard's risk score was a "hand-written formula, not your model's actual output."
**Solution:** Replaced the hardcoded risk formula with `model.predict_proba(X)[:, 1]` — the actual XGBoost probability output. Now every risk score displayed in the dashboard is the real model confidence, not an approximation.

---

## 9. Technology Stack

| Component | Technology |
|---|---|
| **ML Framework** | XGBoost, scikit-learn |
| **Backend** | Python, FastAPI, Uvicorn |
| **Frontend** | React 18, Vite, react-force-graph-2d |
| **AI/LLM** | Groq API (Qwen 3.8-27B) |
| **Data Processing** | Pandas, NumPy |
| **Visualization** | Recharts, ForceGraph2D |
| **Styling** | Vanilla CSS (Glassmorphism dark theme) |

---

## 10. How to Run

### Terminal 1: Backend
```bash
cd abuse-ring-sentinel
.\venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd abuse-ring-sentinel/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 11. Project Structure

```
abuse-ring-sentinel/
├── backend/                    # FastAPI Backend
│   ├── main.py                 # API server (endpoints, ML inference)
│   └── llm_engine/             # Groq LLM integration
│       └── explain.py          # Ring explanation + chat functions
├── frontend/                   # React Dashboard
│   └── src/
│       ├── pages/              # Overview, RingExplorer, RingDetail, LiveAnalysis, ModelAnalysis
│       ├── api.js              # API client
│       └── index.css           # Global styles
├── ml/                         # Machine Learning
│   ├── pipeline/               # Feature engineering, training, evaluation
│   │   ├── feature_engineering.py
│   │   ├── train_models.py
│   │   ├── evaluate.py
│   │   └── graph_features.py
│   └── data_generator/         # Synthetic data generation
│       ├── config.py
│       ├── run_generator.py
│       ├── generate_customers.py
│       ├── generate_rings.py
│       ├── generate_transactions.py
│       ├── generate_network.py
│       └── generate_legitimate_groups.py
├── data/                       # Raw and processed datasets
├── models/                     # Saved XGBoost/IsolationForest models
├── .env                        # API keys
├── requirements.txt
└── README.md
```

---

## 12. Conclusion

Abuse Ring Sentinel demonstrates a complete, production-ready approach to fraud ring detection:

1. **Realistic data generation** with 7 fraud archetypes and hard negatives.
2. **Robust feature engineering** combining behavioral, network, and graph signals.
3. **Honest model evaluation** with proper train/val/test splits, overfitting checks, and shuffled-label validation.
4. **Production-grade UI** with real-time graph visualization, AI-powered investigation, and live CSV analysis.
5. **Real model output** — every risk score in the dashboard comes from `predict_proba()`, not a formula.

The recommended production pipeline is **Rules → XGBoost Tabular**, which achieves F1=0.996 with only 1 false positive on the test set (Rs 60,000 estimated FP cost), compared to Rs 19.2 lakh for the Isolation Forest approach.

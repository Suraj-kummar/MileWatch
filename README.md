# 🚚 MileWatch: Delivery Attempt Credibility Scorer

## 📖 Overview
**MileWatch** is an end-to-end microservices application that dynamically scores the credibility of last-mile delivery attempts using Machine Learning. It prevents "fake delivery attempts" by evaluating real-time features like GPS distance, attempt timing, executive history, and call logs. Rather than just returning an arbitrary number, MileWatch uses **Explainable AI (SHAP)** to provide human-readable reasons (e.g., *"Executive was 2.3km away"*) and automatically drafts dispute emails for suspicious attempts.

---

## 🏗️ Architecture
MileWatch uses a robust, 3-tier microservice architecture to decouple the presentation, orchestration, and inference layers:

1. **React Frontend (Vite):** A professional, responsive dark-themed dashboard for real-time attempt monitoring, interactive credibility score visualization (dynamic gauges and reason cards), and historic attempt filtering.
2. **Spring Boot Backend (API Gateway):** A Java 17 service acting as the central orchestrator. It manages API requests from the frontend, persists data locally, and reliably manages network requests to the ML service. 
3. **ML Microservice (Flask):** A dedicated Python API serving an XGBoost model. It handles continuous feature scaling, model inference, SHAP-based feature impact extraction (reason generation), and LLM/template-focused Dispute Draft generation.

---

## ✨ Key Features
- **Intelligent Credibility Scoring:** Uses targeted, realistic synthetic data generation (5 distinct behavioral profiles) and a hyperparameter-tuned **XGBoost regression model** to accurately calculate attempt credibility.
- **Explainable AI (SHAP):** Every single credibility score comes with the top 3-5 dynamically calculated reasons, ensuring full transparency on *why* a particular credibility score was assigned.
- **Automated Dispute Generator:** Enhances human-action capabilities by instantly structuring context-aware dispute drafts using the generated credibility data and exact SHAP reasons.
- **Enterprise UI & Dashboard Engine:** Check real-time system health via total attempts, average credibility scores, flagged counts, and dispute rates. Drill down easily to specific attempts or manually submit entries.

---

## 🚀 Getting Started

Follow these steps to run the complete MileWatch stack locally.

### 1. Database Setup (Zero Config!)
Good news! The backend operates cleanly with an **embedded H2 Database**. You don't need to install or configure PostgreSQL or handle Docker containers. Everything is self-contained. The data is written to `./backend/data/milewatch-db` allowing state to survive server restarts.

### 2. Machine Learning Service (Flask API)
This service houses the core algorithmic intelligence. It must be spun up on Port `5000`.
**Prerequisites:** Python 3.9+

```bash
cd ml-service

# Create and activate a Virtual Environment
python -m venv venv

# On Mac/Linux:
source venv/bin/activate  
# On Windows:
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# [Optional] Generating the model
# The artifacts (xgb_model.json, feature_scaler.pkl) may already exist in model/artifacts/. 
# If not, generate the data and train the model via:
python data/generator.py
python model/features.py
python model/train.py

# Start the Flask Application
python service/app.py
```
*Your ML API should now be running at `http://localhost:5000`*

### 3. Backend Service (Spring Boot)
The centralized coordination layer and gateway. It must be spun up on Port `8080`.
**Prerequisites:** Java 17+, Maven

```bash
cd backend

# Build and run the service via Maven
mvn clean install
mvn spring-boot:run
```
*Your Spring Boot backend should now be running at `http://localhost:8080`*

### 4. Frontend Dashboard (React + Vite)
The user interface. It needs to spin up on Port `5173`.
**Prerequisites:** Node.js (v18+)

```bash
cd frontend

# Install necessary modules
npm install

# Start up the Vite development server
npm run dev
```
*Your Dashboard should now be running at `http://localhost:5173`*

---

## 📂 Repository Structure
```text
MileWatch/
├── ml-service/                    # Python — Data + Model + Flask API
│   ├── data/                      # Realistic data generation and behavioral profiling
│   ├── model/                     # Feature scaling, XGBoost training, SHAP explainers
│   ├── service/                   # Flask API, prediction logic, dispute composition
│   ├── tests/                     # Unit and integration verification
│   └── requirements.txt     
│
├── backend/                       # Java 17 — Spring Boot API Gateway
│   ├── src/main/java/com/milewatch/
│   │   ├── controller/            # REST Endpoints for attempts & aggregation
│   │   ├── service/               # Core business logic & Flask ML WebClient
│   │   ├── model/                 # Entities, Enums, DTOs
│   │   └── repository/            # API Data JPA (H2 integration)
│   ├── src/main/resources/        # application.yml and SQL schemas
│   └── pom.xml
│
└── frontend/                      # React 19 — Dashboard UI
    ├── src/
    │   ├── components/            # Reusable Widgets (ScoreGauge, ReasonCards, Stats)
    │   ├── pages/                 # Full Screen Views (Dashboard, History)
    │   └── services/              # API Client Connectors (Axios)
    ├── package.json
    └── index.css                  
```

---

## 🛠️ Extensive Tech Stack
- **Frontend UI**: React 19, Vite, Vite Plugin React, React Router Dom, Lucide Icons, plain CSS.
- **Backend Architecture**: Java 17, Spring Boot 3.4.4, Spring Web REST API, Spring Data JPA, H2 Database (File-Embedded), Lombok, Jackson.
- **Machine Learning**: Python 3, XGBoost 2.1, SHAP Explainers, Scikit-Learn (Scalers & Utilities), Pandas, NumPy, Joblib, PyTest.
- **ML Wrapping**: Flask Web Framework.

---

## 📊 Dataset & Model Deep-dive
The underlying dataset mimics real deliveries using 5 meticulously defined human-behavior archetypes (`Genuine`, `Borderline`, `Lazy Skip`, `Shift-end Dump`, `Systematic Fraud`).

The feature engineering layer evaluates the following columns:
1. `gps_distance_m`: How far the rider was from drop-off.
2. `time_gap_minutes`: Operational constraints vs mark instances.
3. `call_made`: Binary boolean of execution reality.
4. `is_cod`: Risk stratification across payment lines.
5. `exec_historical_fake_rate`: Overall delivery track record.
6. `minutes_to_shift_end`: Attempted to catch end-of-shift offloads.
7. `pincode_tier`: Geographical impact tiers.

The **XGBoost regressor** executes these inputs to return a float output scoring map strictly constrained to `0.0` (Fraudulent/Lazy) to `1.0` (Genuine).

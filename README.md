# 🚂 RailMadat — Railway Maintenance Coordination System

> A smart, AI-powered railway maintenance management system for Indian Railways.

<p align="center">
  <strong>Smart India Hackathon 2026-27</strong>
</p>

---

## 📋 Table of Contents

- [About](#-about)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Tech Stack](#-tech-stack)
- [User Roles](#-user-roles)
- [API Documentation](#-api-documentation)
- [ML Model](#-ml-model)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 About

RailMadat is an intelligent railway maintenance coordination system designed to streamline fault reporting, verification, and maintenance scheduling for Indian Railways. It leverages AI/ML for fault classification, safety-first prioritization, and automated scheduling while ensuring complete audit trails and accountability.

### Problem Statement

- Railway assets (tracks, signals, electrical equipment) fail regularly
- Public complaints often go unnoticed or untracked
- Maintenance teams lack real-time information about faults
- No centralized system for tracking maintenance history
- Safety-critical issues may not get immediate attention

### Solution

RailMadat provides:
- **Easy Complaint Registration** — Public and staff can report faults
- **Inspector Verification** — Technical staff verify complaints before processing
- **AI Classification** — ML model categorizes and prioritizes faults
- **Safety-First Scheduling** — Critical assets get immediate attention
- **Complete Audit Trail** — Every action is logged
- **Real-Time Tracking** — Track complaint status from report to resolution

## 📁 Project Structure

```
RailMadat/
├── railmadat-frontend/          # HTML/CSS/JS frontend (Vercel)
│   ├── *.html                   # 20 pages (dashboard, complaints, etc.)
│   ├── assets/css/              # Theme, layout, components
│   ├── assets/js/               # App logic, auth, API client
│   └── vercel.json              # Vercel deployment config
│
├── backend/                     # FastAPI backend (Render)
│   ├── app/api/                 # 12 route modules
│   ├── app/authentication/      # JWT auth
│   ├── app/database/            # Supabase client
│   ├── app/data_services/       # Business logic
│   ├── app/contracts/           # Pydantic models
│   ├── scripts/                 # Admin setup, CSV import
│   ├── tests/                   # Backend tests
│   └── requirements.txt
│
├── ml/                          # AI/ML fault classification
│   └── maintenance_intelligence/
│       ├── training/            # Model training scripts
│       ├── datasets/            # Training data
│       ├── model_artifacts/     # Trained models (.joblib)
│       ├── tests/               # 30+ test files
│       └── sample_payloads/     # Example API inputs/outputs
│
├── csv_data/                    # Raw CSV data files
│   ├── asset_master.csv         # 26 railway assets
│   ├── teams.csv                # 5 maintenance teams
│   ├── maintenance_history.csv  # 40 maintenance records
│   ├── maintenance_schedules.csv
│   ├── maintenance_status_history.csv
│   ├── work_completion_reports.csv
│   ├── equipment.csv
│   └── role4_maintenance_classification_dataset.csv
│
├── supabase/                    # Database migrations
│   ├── migrations/              # SQL setup scripts
│   └── seed/                    # Seed data
│
├── analytics/                   # Maintenance analytics
├── docs/                        # Documentation
├── scripts/                     # Root-level utilities
│
├── start.bat                    # Windows: start both servers
├── start.sh                     # Linux/Mac: start both servers
├── test_endpoints.py            # API endpoint tests
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Modern web browser
- Supabase account (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/railmadat.git
cd railmadat
```

### 2. Set up the backend

```bash
cd backend
cp .env.example .env
# Edit .env with your Supabase credentials
pip install -r requirements.txt
```

### 3. Start everything

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Or manually:**
```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd railmadat-frontend
python -m http.server 3000
```

### 4. Open in browser

| URL | What |
|-----|------|
| `http://localhost:3000` | Frontend |
| `http://localhost:8000` | Backend API |
| `http://localhost:8000/docs` | API Documentation |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, JavaScript ES6+ (vanilla) |
| **Backend** | Python 3.9+, FastAPI |
| **Database** | PostgreSQL via Supabase |
| **Auth** | Supabase Auth + JWT |
| **AI/ML** | scikit-learn, pandas, numpy |
| **Hosting** | Vercel (frontend), Render (backend) |

## 👥 User Roles

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Administrator | `admin@railmadat.in` | `admin123` | Full system access |
| Inspector | `inspector1@railmaintain.in` | `inspector123` | Verify/reject complaints |
| Manager | `manager.signal@railmaintain.in` | `manager123` | Approve blocks, manage teams |
| Staff | `staff1.signal@railmaintain.in` | `staff123` | View tasks, submit reports |
| Reporter | `reporter1@railmaintain.in` | `reporter123` | File complaints, track status |

## 🔌 API Documentation

Full interactive docs at `http://localhost:8000/docs` (Swagger UI).

### Key Endpoints

```
POST   /api/auth/login              # Login
GET    /api/auth/me                 # Current user profile

GET    /api/complaints              # List complaints
POST   /api/complaints              # Create complaint
GET    /api/complaints/:id          # Complaint details

GET    /api/workflow/history        # Status change timeline
GET    /api/tasks                   # Maintenance tasks
GET    /api/dashboard/stats         # Dashboard statistics
GET    /api/dashboard/alerts        # AI classification alerts
GET    /api/teams                   # Team management
GET    /api/schedules               # Maintenance schedules
GET    /api/assets                  # Asset registry
```

## 🤖 ML Model

The `ml/` directory contains the AI fault classification system:

- **Training**: `ml/maintenance_intelligence/training/`
- **Model**: `ml/maintenance_intelligence/model_artifacts/maintenance_classifier.joblib`
- **Tests**: 30+ test files covering edge cases, adversarial inputs, safety
- **Sample I/O**: `ml/maintenance_intelligence/sample_payloads/`

```bash
# Run ML tests
cd ml
python -m pytest maintenance_intelligence/tests/ -v
```

## 🗄️ Database

Supabase project with 11 tables:

| Table | Records | Purpose |
|-------|---------|---------|
| `users` | 11 | User profiles |
| `complaints` | 26 | Fault reports |
| `maintenance_tasks` | 48 | Assigned work |
| `maintenance_history` | 40 | Past records |
| `maintenance_schedules` | 20 | Planned maintenance |
| `maintenance_status_history` | 110 | Workflow changes |
| `work_completion_reports` | 20 | Work done |
| `asset_registry` | 26 | Railway assets |
| `equipment` | 5 | Testing equipment |
| `maintenance_teams` | 5 | Team assignments |
| `ai_classifications` | 6 | ML predictions |

SQL migrations: `supabase/migrations/`

## 🚢 Deployment

### Frontend (Vercel)

```bash
cd railmadat-frontend
git init && git add . && git commit -m "v1.0"
# Push to GitHub, then import on vercel.com
```

### Backend (Render)

```bash
cd backend
# Push to GitHub, then create Web Service on render.com
# Build: pip install -r requirements.txt
# Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment Variables (Production)

Set these in Render/Vercel dashboard:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret
JWT_SECRET=your-app-secret
CORS_ORIGINS=https://railmadat.vercel.app
DATA_MODE=supabase
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License — see [LICENSE](railmadat-frontend/LICENSE) for details.

## 📞 Contact

**RailMadat Team** — Smart India Hackathon 2026-27

**Built with ❤️ for Indian Railways**

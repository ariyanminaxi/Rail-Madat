# 🚂 RailMadat Backend

> FastAPI + Supabase backend for the Railway Maintenance Coordination System.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Supabase project (database + auth)

### Setup

1. **Clone and install**
```bash
git clone https://github.com/yourusername/railmadat-backend.git
cd railmadat-backend
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. **Run the server**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Open API docs**
```
http://localhost:8000/docs
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings from .env
│   ├── api/                       # Route handlers
│   │   ├── auth_routes.py         # Login, register, profile
│   │   ├── complaint_routes.py    # CRUD complaints
│   │   ├── inspection_routes.py   # Verify/reject complaints
│   │   ├── task_routes.py         # Maintenance tasks
│   │   ├── workflow_routes.py     # Status history timeline
│   │   ├── dashboard_routes.py    # Stats, alerts
│   │   ├── team_routes.py         # Team management
│   │   ├── scheduling_routes.py   # Maintenance schedules
│   │   ├── asset_routes.py        # Asset registry
│   │   ├── audit_routes.py        # Audit logs
│   │   └── health_routes.py       # Health check
│   ├── authentication/            # JWT auth
│   ├── contracts/                 # Pydantic models
│   ├── database/                  # Supabase client
│   ├── data_services/             # Business logic
│   └── audit/                     # Audit logging
│
├── scripts/                       # Utility scripts
│   ├── create_admin.py            # Create admin user
│   ├── create_all_auth_users.py   # Create all test accounts
│   ├── csv_to_supabase.py         # Import CSV data
│   ├── upload_csv_data.py         # Upload CSV to Supabase
│   └── migrate_database.py        # Database migrations
│
├── data/                          # CSV data files (5KB)
│   ├── reference/                 # Asset registry
│   ├── planning/                  # Schedules
│   ├── execution/                 # History
│   └── workflow/                  # Status history
│
├── tests/                         # Test files
├── docs/                          # Documentation
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── .gitignore
```

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | ✅ |
| `SUPABASE_JWT_SECRET` | JWT secret for auth | ✅ |
| `JWT_SECRET` | App JWT secret | ✅ |
| `CORS_ORIGINS` | Allowed frontend URLs | ✅ |
| `DATA_MODE` | `supabase` or `csv` | Optional |

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/login          # Login (returns JWT)
GET    /api/auth/me             # Get current user profile
POST   /api/auth/logout         # Logout
```

### Complaints
```
GET    /api/complaints          # List all complaints
POST   /api/complaints          # Create new complaint
GET    /api/complaints/:id      # Get complaint details
```

### Workflow
```
GET    /api/workflow/history    # Status change timeline
```

### Tasks
```
GET    /api/tasks               # List maintenance tasks
POST   /api/tasks/:id/start     # Start a task
POST   /api/tasks/:id/complete  # Complete a task
```

### Dashboard
```
GET    /api/dashboard/stats     # Statistics (counts, metrics)
GET    /api/dashboard/alerts    # AI classification alerts
```

### Teams
```
GET    /api/teams               # List teams
GET    /api/teams/:id           # Team details
```

### Scheduling
```
GET    /api/schedules           # Maintenance schedules
POST   /api/schedules           # Create schedule
```

### Assets
```
GET    /api/assets              # Asset registry
GET    /api/assets/:id          # Asset details
```

### Inspections
```
POST   /api/inspections/verify  # Verify complaint (Inspector)
POST   /api/inspections/reject  # Reject complaint (Inspector)
GET    /api/inspections/pending # Pending inspections
```

### Audit
```
GET    /api/audit/logs          # Audit trail
```

## 👥 Test Accounts

Created via `scripts/create_all_auth_users.py`:

| Role | Email | Password |
|------|-------|----------|
| Administrator | `admin@railmadat.in` | `admin123` |
| Inspector | `inspector1@railmaintain.in` | `inspector123` |
| Inspector | `inspector2@railmaintain.in` | `inspector123` |
| Manager | `manager.signal@railmaintain.in` | `manager123` |
| Manager | `manager.track@railmaintain.in` | `manager123` |
| Staff | `staff1.signal@railmaintain.in` | `staff123` |
| Staff | `staff1.track@railmaintain.in` | `staff123` |
| Reporter | `reporter1@railmaintain.in` | `reporter123` |
| Reporter | `reporter2@railmaintain.in` | `reporter123` |

## 🗄️ Database Tables

| Table | Purpose |
|-------|---------|
| `users` | User profiles with roles |
| `complaints` | Fault reports |
| `maintenance_tasks` | Assigned work |
| `maintenance_history` | Past maintenance records |
| `maintenance_schedules` | Planned maintenance |
| `maintenance_status_history` | Workflow status changes |
| `work_completion_reports` | Work done reports |
| `asset_registry` | Railway assets |
| `equipment` | Testing equipment |
| `maintenance_teams` | Team assignments |
| `ai_classifications` | ML fault classification |

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 🚢 Deployment

### Render
1. Connect GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

### Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for Indian Railways — Smart India Hackathon 2026-27**

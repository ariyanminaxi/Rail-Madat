# 🚂 RailMadat — Project Progress & Info

## Project Overview

**RailMadat** is a Railway Maintenance Coordination System built for Smart India Hackathon 2026-27. It's a full-stack web app with AI-powered fault classification, role-based access, and complete audit trails.

**GitHub:** https://github.com/ariyanminaxi/Rail-Madat
**Frontend:** https://railmadat.vercel.app
**Backend API:** https://rail-madat-backend.onrender.com
**API Docs:** https://rail-madat-backend.onrender.com/docs

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript ES6+ (vanilla — no React) |
| Backend | Python 3.9+, FastAPI |
| Database | PostgreSQL via Supabase |
| Auth | Supabase Auth + JWT |
| AI/ML | scikit-learn, pandas, numpy |
| Hosting | Vercel (frontend), Render (backend) |

---

## Project Structure

```
RailMadat/
├── railmadat-frontend/          # 20 HTML pages + CSS + JS
├── backend/                     # FastAPI with 12 route modules
├── ml/                          # AI fault classification (30+ tests)
├── csv_data/                    # 8 CSV data files
├── supabase/                    # SQL migrations
├── analytics/                   # Maintenance analytics
├── scripts/                     # Root utilities
├── docs/                        # Documentation
├── .github/workflows/ci.yml     # CI (manual trigger only)
├── start.bat / start.sh         # Start both servers
└── README.md                    # Full project docs
```

---

## What's Built & Working

### Frontend (20 Pages)

| Page | Status | Description |
|------|--------|-------------|
| `login.html` | ✅ Working | Email/password login, redirects by role |
| `dashboard.html` | ✅ Working | Stats cards, recent complaints, tasks, AI alerts |
| `complaints.html` | ✅ Working | Full table with filters, priority, links to details |
| `complaint-details.html` | ✅ Working | Full complaint info + workflow timeline |
| `new-complaint.html` | ✅ Working | Reporter files fault with description, location, asset |
| `settings.html` | ✅ Working | Real profile from API, change password, notifications |
| `notifications.html` | ✅ Working | Loads real dashboard alerts |
| `inspections.html` | ✅ Working | Pending inspections with filters |
| `assigned-tasks.html` | ✅ Working | Staff task list |
| `work-completion.html` | ✅ Working | Work completion form |
| `pending-approvals.html` | ✅ Working | Manager approval queue |
| `bundle-approvals.html` | ✅ Working | Bundle approval |
| `maintenance-schedule.html` | ✅ Working | Schedule view |
| `team-management.html` | ✅ Working | Team assignments |
| `profile.html` | ✅ Working | User profile |
| `about.html` | ✅ Working | About page |
| `contact.html` | ✅ Working | Contact page |
| `404.html` | ✅ Working | Not found page |
| `unauthorized.html` | ✅ Working | 403 page |
| `index.html` | ✅ Working | Landing page |

### Backend (12 Route Modules)

| Route | Endpoints | Status |
|-------|-----------|--------|
| `/api/auth/*` | login, me, logout | ✅ Working |
| `/api/complaints/*` | list, create, detail | ✅ Working |
| `/api/workflow/*` | history (timeline) | ✅ Working |
| `/api/tasks/*` | list, start, complete | ✅ Working |
| `/api/dashboard/*` | stats, alerts | ✅ Working |
| `/api/teams/*` | list, detail | ✅ Working |
| `/api/schedules/*` | list, create | ✅ Working |
| `/api/assets/*` | list, detail | ✅ Working |
| `/api/inspections/*` | verify, reject, pending | ✅ Working |
| `/api/audit/*` | logs | ✅ Working |
| `/api/health/*` | health check | ✅ Working |

### Key Features

- ✅ Dark/Light theme toggle (persisted in localStorage)
- ✅ Role-based sidebar navigation (5 roles)
- ✅ Auto-detect localhost vs production API URL
- ✅ 24-hour clock format (IST timezone)
- ✅ Workflow timeline with status transitions
- ✅ Complaint submission from reporter role
- ✅ AI classification panel on dashboard
- ✅ Responsive design (mobile-friendly)
- ✅ CORS configured for Vercel ↔ Render
- ✅ Error handling with user-friendly messages

---

## User Accounts

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

---

## Database (Supabase)

**Project:** `syxtsauhtauyedbwneue`

| Table | Records | Description |
|-------|---------|-------------|
| `users` | 11 | User profiles with roles |
| `complaints` | 26+ | Fault reports |
| `maintenance_tasks` | 48 | Assigned work |
| `maintenance_history` | 40 | Past maintenance records |
| `maintenance_schedules` | 20 | Planned maintenance |
| `maintenance_status_history` | 110 | Workflow status changes |
| `work_completion_reports` | 20 | Work done reports |
| `asset_registry` | 26 | Railway assets |
| `equipment` | 5 | Testing equipment |
| `maintenance_teams` | 5 | Team assignments |
| `ai_classifications` | 6 | ML predictions |

**SQL Migrations:** `supabase/migrations/`

---

## Deployment Status

### ✅ GitHub — DONE
- Repo: https://github.com/ariyanminaxi/Rail-Madat
- All code pushed (backend, frontend, ML, CSV data, scripts)
- `.gitignore` blocks `.env`, `__pycache__`, logs
- CI workflow (manual trigger only)

### ✅ Render (Backend) — DONE
- URL: https://rail-madat-backend.onrender.com
- Environment variables set:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_JWT_SECRET`, `JWT_SECRET`
  - `CORS_ORIGINS=https://railmadat.vercel.app`
  - `DATA_MODE=supabase`
- Login API tested and working

### ✅ Vercel (Frontend) — DONE (auto-deploys from GitHub)
- URL: https://railmadat.vercel.app
- Root Directory: `railmadat-frontend`
- API auto-detects: localhost → `localhost:8000`, deployed → `rail-madat-backend.onrender.com`

---

## Bugs Fixed

| Bug | Fix |
|-----|-----|
| Login "no role assigned" | Created missing `users` table rows for all accounts |
| Complaint submission 500 error | Removed FK constraint on `asset_id`, added `priority` column |
| Clock showing 12-hour format | Changed to 24-hour format in app.js |
| Workflow timeline empty | Created `/api/workflow/history` endpoint, fixed column mapping |
| Dark mode not working on some pages | Migrated 11 pages from old layout to new `app.js` pattern |
| Settings showing placeholder | Rewrote to load real profile from `/api/auth/me` |
| Complaints missing columns | Added Priority, Asset ID, View links to table |
| CORS errors on POST | Added try/except with proper error response in complaint routes |
| Production API URL wrong | Fixed URL from `railmadat-backend` to `rail-madat-backend` |
| Vercel deploy blocked | Fixed git config username to match GitHub account |

---

## SQL Run in Supabase

```sql
-- Added priority column to complaints
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'Medium';

-- Added rejection fields
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE complaints ADD COLUMN IF NOT EXISTS rejected_by TEXT;

-- Dropped FK constraint so complaints can reference any asset
ALTER TABLE complaints DROP CONSTRAINT IF EXISTS complaints_asset_id_fkey;
```

---

## Environment Variables

### Backend (.env / Render)
```
SUPABASE_URL=https://syxtsauhtauyedbwneue.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=0cd0829b-9ee9-4f91-bf71-bf20f3d94304
JWT_SECRET=railmadat-production-secret-key-2026
CORS_ORIGINS=https://railmadat.vercel.app
DATA_MODE=supabase
```

### Frontend (api.js)
```javascript
// Auto-detects environment
const _isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_BASE = _isLocal
    ? 'http://localhost:8000/api'
    : 'https://rail-madat-backend.onrender.com/api';
```

---

## How to Run Locally

```bash
# Start everything
cd D:/VS_code/RailMadat
start.bat          # Windows
# or
./start.sh         # Linux/Mac

# Or manually:
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend
cd railmadat-frontend
python -m http.server 3000
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Pending / Known Issues

1. **Vercel deploy blocked** — GitHub committer mismatch on Hobby plan (previous deploy works)
2. **Some pages are stubs** — maintenance-schedule, pending-approvals, bundle-approvals show basic layout but limited data
3. **No real images/icons** — sidebar uses emoji icons, no custom SVG icons uploaded
4. **ML model not integrated into backend** — classifier exists in `ml/` but backend doesn't call it on complaint creation
5. **No file upload** — complaint form doesn't support photo uploads yet
6. **No email notifications** — notification_rules.py exists but not wired up

---

## Team

- **GitHub:** ariyanminaxi
- **Project:** RailMadat — Smart India Hackathon 2026-27
- **Built with:** ❤️ for Indian Railways

# 🚂 RailMadat - Railway Maintenance Coordination System

> A smart, AI-powered railway maintenance management system for Indian Railways.

<p align="center">
  <img src="assets/images/logo.png" alt="RailMadat Logo" width="200">
</p>

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Live Demo](#-live-demo)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [API Integration](#-api-integration)
- [User Roles](#-user-roles)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

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
- **Easy Complaint Registration** — Public and staff can report faults via web/mobile
- **Inspector Verification** — Technical staff verify complaints before processing
- **AI Classification** — Smart system automatically categorizes and prioritizes faults
- **Safety-First Scheduling** — Critical assets get immediate attention
- **Complete Audit Trail** — Every action is logged for accountability
- **Real-Time Tracking** — Track complaint status from report to resolution

## ✨ Features

### For Reporters (Public/Staff)
- 📝 Easy complaint registration with photos and location
- 📊 Real-time status tracking of complaints
- 🔔 Notifications on status updates
- 📱 Mobile-friendly responsive design

### For Inspectors
- ✅ Verify/reject complaints with GPS and photos
- 📍 Location-based inspection assignments
- 📋 Inspection history and reports

### For Maintenance Staff
- 📋 View assigned tasks automatically
- ⏱️ Track work progress and time spent
- 📝 Submit completion reports

### For Managers
- ✅ Approve/reject maintenance blocks
- 📅 View and modify maintenance schedules
- 👥 Manage team assignments
- 📊 Dashboard with key metrics and alerts

### For Administrators
- 🔧 Full system access and configuration
- 👥 User management across all roles
- 📈 System-wide analytics and reports

### System Features
- 🌙 Dark/Light theme toggle
- 🔐 Role-based access control
- 📱 Fully responsive design
- ⚡ Real-time updates
- 🔒 Secure authentication via Supabase
- 🎨 IRCTC-inspired professional UI
- 🌍 IST timezone support (24-hour format)

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic markup |
| **CSS3** | Styling with CSS variables for theming |
| **JavaScript ES6+** | Vanilla JS — no frameworks |

### Backend (Separate)
| Technology | Purpose |
|------------|---------|
| **Python 3.9+** | Programming language |
| **FastAPI** | Web framework |
| **Supabase** | Database & Authentication |
| **scikit-learn** | AI/ML fault classification |

### Database
| Technology | Purpose |
|------------|---------|
| **PostgreSQL** (via Supabase) | Data storage |
| **Row Level Security** | Data protection |

### Deployment
| Service | Purpose |
|---------|---------|
| **Vercel** | Frontend hosting |
| **Render** | Backend hosting |
| **Supabase** | Database, Auth, Storage |

## 🌐 Live Demo

- **Frontend**: [https://railmadat.vercel.app](https://railmadat.vercel.app)
- **Backend API**: [https://railmadat-backend.onrender.com](https://railmadat-backend.onrender.com)
- **API Docs**: [https://railmadat-backend.onrender.com/docs](https://railmadat-backend.onrender.com/docs)

### Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Administrator | `admin@railmadat.in` | `admin123` |
| Inspector | `inspector1@railmaintain.in` | `inspector123` |
| Maintenance Manager | `manager.signal@railmaintain.in` | `manager123` |
| Maintenance Staff | `staff1.signal@railmaintain.in` | `staff123` |
| Reporter | `reporter1@railmaintain.in` | `reporter123` |

> ⚠️ **Note**: This is a prototype system with synthetic test data. All records are synthetic and not real railway data.

## 📁 Project Structure

```
railmadat-frontend/
├── index.html                    # Landing page
├── login.html                    # Login page
├── dashboard.html                # Role-based dashboard
├── complaints.html               # Complaints list
├── new-complaint.html            # Complaint registration
├── complaint-details.html        # Complaint details + workflow timeline
├── assigned-tasks.html           # Maintenance staff tasks
├── work-completion.html          # Work completion report
├── pending-approvals.html        # Manager approvals
├── bundle-approvals.html         # Bundle approvals
├── maintenance-schedule.html     # Maintenance schedule
├── team-management.html          # Team management
├── inspections.html              # Inspector dashboard
├── settings.html                 # User settings
├── notifications.html            # Notifications
├── profile.html                  # User profile
├── about.html                    # About page
├── contact.html                  # Contact page
├── 404.html                      # Not found
├── unauthorized.html             # Access denied
│
├── assets/
│   ├── css/
│   │   ├── main.css              # Global styles, reset, typography
│   │   ├── theme.css             # Dark/light theme variables
│   │   ├── layout.css            # Header, sidebar, footer
│   │   ├── components.css        # Badges, tables, cards, forms, modals
│   │   └── pages/
│   │       └── login.css         # Login page styles
│   │
│   ├── js/
│   │   ├── app.js                # App init, sidebar, topbar, clock, nav
│   │   ├── auth.js               # Login, logout, token management
│   │   ├── api.js                # API client (auto-detects localhost/production)
│   │   ├── theme.js              # Theme toggle helper
│   │   ├── utils.js              # Date formatting, validators, helpers
│   │   └── pages/
│   │       ├── dashboard.js      # Dashboard logic
│   │       └── complaints.js     # Complaints list logic
│   │
│   └── images/
│       ├── favicon.svg           # Browser tab icon
│       └── icons/                # SVG icons (future)
│
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment variable template
├── vercel.json                   # Vercel deployment config
├── LICENSE                       # MIT License
└── README.md                     # This file
```

## 🚀 Getting Started

### Prerequisites

- Modern web browser (Chrome, Firefox, Edge)
- (Optional) Python 3 or Node.js for local server

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/railmadat-frontend.git
cd railmadat-frontend
```

2. **Start a local server**
```bash
# Using Python
python -m http.server 3000

# Using Node.js
npx serve .

# Or use VS Code Live Server extension
```

3. **Open in browser**
```
http://localhost:3000
```

No build step required — the project uses vanilla HTML/CSS/JS.

## 💻 Usage

### Reporter Flow
1. Login → **New Complaint** → Fill details → Submit
2. Track via **My Complaints** → Click ID for details + timeline

### Inspector Flow
1. Login → **Pending Inspections** → Verify/Reject complaints
2. Add inspection notes and mark status

### Staff Flow
1. Login → **Assigned Tasks** → Start work → Submit completion report

### Manager Flow
1. Login → **Pending Approvals** → Approve/Reject blocks
2. View **Maintenance Schedule** and **Team Management**

### Admin Flow
1. Login → Full access to all features
2. **Settings** → System configuration

## 🔌 API Integration

### Auto-Detection
The `api.js` file automatically detects the environment:
- **Localhost** → `http://localhost:8000/api`
- **Deployed** → `https://railmadat-backend.onrender.com/api`

### Key Endpoints

```
POST   /api/auth/login              # User login
GET    /api/auth/me                 # Get current user profile

GET    /api/complaints              # List complaints
POST   /api/complaints              # Create complaint
GET    /api/complaints/:id          # Get complaint details

GET    /api/workflow/history        # Workflow status timeline
GET    /api/tasks                   # List tasks
GET    /api/dashboard/stats         # Dashboard statistics
GET    /api/dashboard/alerts        # AI classification alerts
```

### Authentication
JWT tokens stored in `localStorage`. Auto-redirect to login on 401.

## 👥 User Roles

| Role | Access Level | Key Features |
|------|-------------|--------------|
| **Reporter** | Basic | File complaints, track status |
| **Inspector** | Technical | Verify complaints, inspections |
| **Maintenance Staff** | Operational | View tasks, submit reports |
| **Maintenance Manager** | Managerial | Approve blocks, manage teams |
| **Administrator** | Full | Complete system access |

## 📸 Screenshots

### Landing Page
![Lining Page](assets/images/screenshots/landing.png)

### Dashboard
![Dashboard](assets/images/screenshots/dashboard.png)

### Complaint Registration
![New Complaint](assets/images/screenshots/new-complaint.png)

### Dark Mode
![Dark Theme](assets/images/screenshots/dark-theme.png)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## 📞 Contact

**RailMadat Team** — Built for Smart India Hackathon 2026-27

**Project Links:**
- Frontend: [https://github.com/yourusername/railmadat-frontend](https://github.com/yourusername/railmadat-frontend)
- Backend: [https://github.com/yourusername/railmadat-backend](https://github.com/yourusername/railmadat-backend)

## 🙏 Acknowledgments

- Indian Railways for inspiration and requirements
- [Supabase](https://supabase.com) for backend services
- [Vercel](https://vercel.com) for frontend hosting
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework

---

**Built with ❤️ for Indian Railways**

*Last Updated: August 2026*

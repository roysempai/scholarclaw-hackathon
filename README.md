# ScholarClaw - AI-Powered Scholarship Agent

**Track:** AI/ML Innovation  
**Hackathon Submission:** April 3, 2026

---

## 🎯 Project Overview

ScholarClaw is an AI-powered scholarship matching and application platform that helps students discover and apply for scholarships that match their profile. The system uses multi-agent AI architecture with built-in security features including prompt injection detection, hash-chained audit logging, and policy-based access control.

### Key Features

- 🤖 **AI-Powered Matching**: Intelligent scholarship matching based on student eligibility
- 🔒 **Security-First**: ArmorIQ prompt injection detection, hash-chained audit logs
- 📊 **Real-time Updates**: Automated deadline reminders and application tracking
- 🎓 **Profile-Based Matching**: Match scores calculated based on comprehensive student profiles
- 🔍 **Eligibility Checking**: Automated eligibility verification for schemes
- 📝 **Draft Generation**: AI-assisted application draft creation

---

## 🚀 Deployed Links

- **Frontend (Live)**: https://frontend-gold-omega-16.vercel.app
- **Backend API**: http://localhost:8000 (See setup instructions below)
- **API Documentation**: http://localhost:8000/docs (When backend is running)

---

## 🏗️ Tech Stack

### Frontend
- React 18.3 + Vite 5.2
- React Router v6
- Axios + Tailwind CSS

### Backend
- FastAPI (Python 3.11)
- PostgreSQL 15 + Prisma ORM
- JWT Authentication
- APScheduler (Background jobs)

### AI/ML
- Groq API (LLaMA 3.3 70B)
- Multi-agent orchestration with LangGraph
- Policy-based eligibility engine

### Security
- ArmorIQ (Prompt injection detection)
- Hash-chained audit logging
- Row-level security (PostgreSQL)

---

## 📋 Setup Instructions

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ and npm
- Git

### Quick Start

1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd scholarclaw
```

2. **Set Up Environment Variables**

Create `backend/.env`:
```env
DATABASE_URL=postgresql://scholarclaw:scholarclaw_dev@db:5432/scholarclaw
JWT_SECRET=your_secret_key_here
GROQ_API_KEY=your_groq_api_key_here
SENDGRID_API_KEY=your_sendgrid_key_optional
FRONTEND_URL=http://localhost:5173
```

Create `frontend/.env`:
```env
VITE_API_BASE_URL=/api
```

**⚠️ Note**: See uploaded `.env` file in submission form for actual values.

3. **Start Backend with Docker**
```bash
# Start database and backend
docker-compose up -d

# Check services are running
docker ps

# View logs
docker logs scholarclaw-backend -f
```

4. **Start Frontend**
```bash
cd frontend
npm install
npm run dev
```

5. **Access the Application**
- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🧪 Testing

### Test Credentials

**Regular User:**
```
Email: test@example.com
Password: Test123!@#
```

**Admin User:**
```
Email: admin@example.com
Password: Admin123!@#
```

### Testing Flow

1. Navigate to http://localhost:5174
2. Login with test credentials
3. Complete profile with eligibility data
4. Browse scholarships on dashboard
5. View scheme details and check eligibility
6. View audit logs

### API Testing

```bash
# Health Check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'

# Get Schemes
curl http://localhost:8000/api/schemes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📁 Project Structure

```
scholarclaw/
├── backend/                # FastAPI Backend
│   ├── agents/            # AI Agents (eligibility, draft, reminder)
│   ├── armoriq/          # Prompt injection detection
│   ├── audit/            # Hash-chained audit logging
│   ├── auth/             # JWT authentication
│   ├── orchestrator/     # Multi-agent orchestration
│   ├── policy/           # Policy gate
│   ├── profile/          # Student profiles
│   ├── schemes/          # Scholarship schemes
│   ├── prisma/           # Database schema
│   └── main.py           # Entry point
│
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page components
│   │   └── App.jsx
│   └── package.json
│
├── docker-compose.yml     # Docker setup
└── README.md             # This file
```

---

## 🔒 Security Features

1. **ArmorIQ** - Prompt injection detection
2. **Hash-Chained Audit Logs** - Tamper-evident trail
3. **JWT Authentication** - Secure token-based auth
4. **Role-Based Access Control** - Student/Admin permissions
5. **Attack Logging** - Real-time threat detection

---

## 📊 Key API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token

### Schemes
- `GET /api/schemes` - List schemes
- `GET /api/schemes/{id}` - Scheme details
- `POST /api/schemes/{id}/check-eligibility` - Check eligibility

### Profile
- `GET /api/profile` - Get profile
- `PUT /api/profile` - Update profile

### Audit
- `GET /api/audit/logs` - User audit logs
- `GET /api/audit/attacks` - Attack logs (Admin)

---

## 🐛 Troubleshooting

### Backend Issues
```bash
# Restart containers
docker-compose down && docker-compose up -d

# View logs
docker logs scholarclaw-backend
```

### Database Issues
```bash
# Check database
docker exec scholarclaw-db psql -U scholarclaw -c "SELECT 1"

# Regenerate Prisma
docker exec scholarclaw-backend prisma generate
```

---

## 📚 Documentation Files

- `QUICK_SETUP.md` - Quick setup guide
- `API_KEYS_GUIDE.md` - How to get API keys
- `FINAL_STATUS_REPORT.md` - Complete system status
- `AUDIT_API_STATUS.md` - Audit system docs

---

## ⚠️ Important Notes

1. **`.env` files**: NOT included in repo - see submission form upload
2. **API Keys**: Groq API key required for AI features
3. **Database**: Auto-initialized via Docker
4. **Excludions**: `node_modules`, `__pycache__`, `.env` excluded as per guidelines

---

## 📞 Contact

For questions, reach out on Discord or via submission form.

**Deployment Status**: ✅ Frontend deployed, Backend runs locally

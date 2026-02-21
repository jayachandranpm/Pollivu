# Pollivu — Privacy-First, Real-Time Polling Platform

A cloud-native polling application where creators build polls in seconds, voters participate anonymously without sign-up, and results update in near real-time — all while storing **zero personal data**.

> **Live URL:** [https://jayachandranpm.pythonanywhere.com](https://jayachandranpm.pythonanywhere.com)

---

## ✨ Features

| Category | Features |
|---|---|
| **Core** | Create polls (2–10 options), anonymous voting, near real-time results |
| **AI** | Generate polls with AI (Gemini, OpenAI, Claude), AI-suggested options on edit |
| **Privacy** | Zero PII collection, session-hashed vote dedup, AES-256-GCM encrypted API keys |
| **Sharing** | QR code generation, CSV export, public/unlisted toggle, embeddable iframe widget |
| **Results Control** | Granular sharing toggles (chart, vote list, insights) — creators choose what's public |
| **Real-Time** | Live vote counts & settings sync via short polling (3s interval) |
| **Management** | Dashboard, edit polls, close/reopen, expiration settings, allow vote changes |
| **Security** | CSRF protection, rate limiting, CSP headers, HSTS, PBKDF2-SHA256 passwords |

---

## 🚀 How to Run Locally

### Prerequisites

- **Python** 3.10+
- **MySQL** 8.0+ (or SQLite for quick local testing)
- **pip** (Python package manager)

### 1. Clone & Setup Virtual Environment

```bash
git clone <repo-url>
cd "POLL PAL"

python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# ── Required ──────────────────────────────────────────
SECRET_KEY=your-secret-key-min-32-chars-here
POLLIVU_SALT=your-random-salt-for-encryption

# ── Database (MySQL) ──────────────────────────────────
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=pollivu

# ── Or use SQLite (no MySQL needed) ───────────────────
# DATABASE_URL=sqlite:///polls.db

# ── Environment ──────────────────────────────────────
FLASK_ENV=development

# ── Optional: Redis (for caching & rate limiting) ────
# REDIS_URL=redis://localhost:6379/0
```

### 3. Initialize the Database

```bash
# If using MySQL, create the database first:
mysql -u root -p -e "CREATE DATABASE pollivu;"

# Run migrations
flask db upgrade

# Or create tables directly (if no migration history):
python3 -c "from app import app, db; app.app_context().__enter__(); db.create_all()"
```

### 4. Run the Application

```bash
python3 app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | `dev-secret-key...` | Flask secret for sessions & encryption |
| `POLLIVU_SALT` | ✅ | — | Salt for AES-256 key derivation |
| `DB_USER` | ⬜ | — | MySQL username |
| `DB_PASSWORD` | ⬜ | — | MySQL password |
| `DB_HOST` | ⬜ | — | MySQL host |
| `DB_PORT` | ⬜ | `3306` | MySQL port |
| `DB_NAME` | ⬜ | — | MySQL database name |
| `DATABASE_URL` | ⬜ | `sqlite:///polls.db` | Full DB URI (fallback if MySQL vars unset) |
| `FLASK_ENV` | ⬜ | `development` | `development` or `production` |
| `REDIS_URL` | ⬜ | `memory://` | Redis URL for caching & rate limiting |

---

## 🏗️ Architecture Summary

```
Clients (Browser)
      │
      ▼ HTTPS
┌──────────────────────┐
│   Gunicorn (threads)  │  ← 2 workers × 4 threads
│   ┌────────────────┐  │
│   │  Flask App     │  │
│   │  ├── Auth BP   │  │  ← Blueprints for modular routing
│   │  ├── Polls BP  │  │
│   │  ├── Dashboard │  │
│   │  ├── API BP    │  │
│   │  └── Main BP   │  │
│   │                │  │
│   │  Services:     │  │
│   │  PollService   │  │  ← Business logic layer
│   │  AIService     │  │  ← Multi-provider AI abstraction
│   └────────────────┘  │
│         │    │    │    │
│    ┌────┘    │    └───┐│
│    ▼         ▼        ▼│
│  MySQL    Redis    AI  │
│  (data)   (cache)  APIs│
└──────────────────────┘
```

| Layer | Technology | Why |
|---|---|---|
| **Compute** | Gunicorn on PythonAnywhere | Simple, reliable, no infra management |
| **Framework** | Flask + Jinja2 | Lightweight; no build step; fast page loads |
| **Database** | MySQL 8.0 | Relational integrity for polls→options→votes |
| **Real-time** | Short polling (3s `setInterval`) | Works on all platforms; no thread blocking; uses `updated_at` for change detection |
| **Auth** | Flask-Login + PBKDF2-SHA256 | Session-based; voters need no account |
| **Encryption** | AES-256-GCM | API keys encrypted at rest in database |
| **AI** | Gemini / OpenAI / Claude | User chooses provider in Settings |

> 📄 **Full architecture document:** See [PRODUCT_ARCHITECTURE.md](PRODUCT_ARCHITECTURE.md)

---

## 📁 Project Structure

```
POLL PAL/
├── app.py                    # Flask app factory & middleware
├── config.py                 # Environment-based configuration
├── extensions.py             # Flask extension initialization
├── models.py                 # SQLAlchemy models (User, Poll, PollOption, Vote)
├── forms.py                  # Flask-WTF form definitions
├── utils.py                  # Utility functions (ID generation, hashing, sanitization)
├── encryption.py             # AES-256-GCM encryption module
├── ai_service.py             # Multi-provider AI service (Gemini, OpenAI, Claude)
├── ai_prompts.py             # Centralized AI prompt templates
├── tasks.py                  # Background task utilities
├── Procfile                  # Gunicorn command for deployment
├── requirements.txt          # Python dependencies (16 packages)
├── PRODUCT_ARCHITECTURE.md   # Full architecture & product document
│
├── blueprints/               # Modular route handlers
│   ├── auth/routes.py        #   Login, register, settings
│   ├── dashboard/routes.py   #   User dashboard
│   ├── polls/routes.py       #   Poll CRUD, voting, embed, AI suggest
│   ├── api/routes.py         #   JSON API (AI, live stats, analytics)
│   └── main/routes.py        #   Landing page, public routes
│
├── services/                 # Business logic layer
│   ├── poll_service.py       #   Poll creation, voting, management
│   └── config_validation.py  #   Configuration validators
│
├── templates/                # Jinja2 HTML templates
│   ├── base_app.html         #   Main layout (sidebar nav)
│   ├── base_minimal.html     #   Minimal layout (unauthenticated users)
│   ├── landing.html          #   Public landing page
│   ├── dashboard.html        #   User dashboard
│   ├── create_poll.html      #   Manual poll creation
│   ├── create_poll_ai.html   #   AI-assisted poll creation
│   ├── edit_poll.html        #   Edit existing poll (incl. share toggles)
│   ├── poll.html             #   Voting interface (short-polling enabled)
│   ├── results.html          #   Results with live charts & analytics
│   ├── settings.html         #   AI provider configuration
│   └── auth/                 #   Login & register
│
├── static/
│   ├── css/                  #   Custom stylesheets (no framework)
│   ├── js/                   #   Client-side JavaScript
│   └── images/               #   Logo and assets
│
├── migrations/               # Alembic database migrations
└── tests/                    # Test suite
```

---

## 🚢 Deployment

### PythonAnywhere (Current Production)

1. Push code to GitHub
2. On PythonAnywhere, clone or pull the repo
3. Create a virtualenv with Python 3.12: `mkvirtualenv --python=/usr/bin/python3.12 venv`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up MySQL database in the **Databases** tab
6. Configure WSGI file to point to `app:app`
7. Set environment variables in the WSGI file or `.env`
8. Reload the web app

### Render

1. Push code to GitHub
2. Create a **Web Service** on [Render](https://render.com)
3. Add `runtime.txt` with `python-3.12.x` (avoid Python 3.13+ for compatibility)
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn -w 2 --threads 4 app:app`
6. Add a MySQL database and set environment variables

### Docker (Any Cloud)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "--threads", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
```

---

## 🔐 Privacy & Security

| Principle | Implementation |
|---|---|
| **Zero PII for voters** | No IP logging, no fingerprinting, no tracking cookies |
| **Anonymous vote dedup** | `SHA-256(session_id + poll_id)` — prevents double-voting without identifying users |
| **Encrypted secrets** | API keys stored with AES-256-GCM; passwords hashed with PBKDF2-SHA256 |
| **Input sanitization** | All user input cleaned with Bleach before storage |
| **Rate limiting** | 30 votes/min, 10 AI calls/min, 60 live_stats/min |
| **Security headers** | CSP, HSTS, X-Frame-Options, X-Content-Type-Options on every response |
| **Embed isolation** | Embed route uses permissive CSP (`frame-ancestors *`); all other routes locked to `SAMEORIGIN` |
| **CSRF protection** | All POST forms protected with Flask-WTF CSRF tokens |

---

## 🧪 Running Tests

```bash
source venv/bin/activate
python3 -m pytest tests/ -v
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| Flask | 3.1.2 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-WTF | 1.2.2 | Forms & CSRF |
| Flask-Limiter | 4.1.1 | Rate limiting |
| Flask-Migrate | 4.1.0 | DB migrations |
| Flask-Login | 0.6.3 | Authentication |
| Flask-Caching | 2.3.1 | Response caching |
| gunicorn | 24.1.1 | WSGI server |
| cryptography | 46.0.3 | AES-256 encryption |
| bleach | 6.3.0 | Input sanitization |
| qrcode | 8.2 | QR code generation |
| requests | 2.32.5 | HTTP client (AI APIs) |
| python-dotenv | 1.2.1 | Environment variables |
| email_validator | 2.3.0 | Email validation |
| mysql-connector-python | 9.5.0 | MySQL driver |
| redis | 7.1.0 | Cache backend |

---

## 📝 License

MIT License · See [LICENSE](LICENSE) for details.

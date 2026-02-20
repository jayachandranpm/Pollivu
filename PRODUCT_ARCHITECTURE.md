# Pollivu — Product & Architecture Document

> **Privacy-First, Real-Time Polling Platform**
> Version 1.0 · February 2026

---

## Table of Contents

1. [Problem Definition](#1-problem-definition)
2. [Target Users](#2-target-users)
3. [Core User Flows](#3-core-user-flows)
4. [Feature Scope](#4-feature-scope)
5. [High-Level Architecture](#5-high-level-architecture)
6. [Key Technical Decisions](#6-key-technical-decisions)
7. [Data Model](#7-data-model)
8. [API Design](#8-api-design)
9. [Security Architecture](#9-security-architecture)
10. [Scalability & Growth Path](#10-scalability--growth-path)
11. [Trade-offs & Decisions Log](#11-trade-offs--decisions-log)

---

## 1. Problem Definition

### The Problem

Existing polling tools (Google Forms, Strawpoll, Typeform) suffer from one or more of these issues:

| Pain Point | Impact |
|---|---|
| **Require sign-up to vote** | Drops participation by 40-60 % |
| **Collect PII / track users** | Privacy-aware audiences avoid them |
| **No real-time feedback** | Creators can't see momentum as it happens |
| **Overly complex UIs** | Takes 5+ clicks to create a simple poll |
| **No AI assistance** | Users struggle to craft good questions and options |

### Our Thesis

> A poll that can be **created in 30 seconds**, **voted on without sign-up**, and shows **live results** — all while collecting **zero personal data** — will see significantly higher engagement than existing tools.

### Success Metric

- A registered user can go from idea → live shareable poll in **< 60 seconds**
- A voter can cast their vote in **< 10 seconds** from opening the link
- **Zero PII** stored for voters

---

## 2. Target Users

### Primary: Team Leads & Community Managers

- **Who:** Slack workspace admins, Discord moderators, classroom teachers, startup founders
- **Need:** Quick decision-making with group input (e.g., "Where should we hold the offsite?")
- **Behavior:** Creates 2–5 polls per week; shares via link in chat/email

### Secondary: Anonymous Voters

- **Who:** Anyone with the poll link
- **Need:** Cast a vote quickly without creating an account or revealing identity
- **Behavior:** One-time visitor; arrives via shared link; leaves after voting

### Persona

| Attribute | Creator ("Priya") | Voter ("Arjun") |
|---|---|---|
| Tech comfort | Moderate | Low–High |
| Account needed | ✅ Yes (to manage polls) | ❌ No |
| Core action | Create → Share → Analyze | Click link → Vote → See results |
| Time budget | 60 seconds | 10 seconds |

---

## 3. Core User Flows

### Flow 1 — Poll Creation (Authenticated)

```
Landing Page → Register / Login → Dashboard
    → "Create Poll" → Enter question + options
    → Set expiration, visibility, vote-change rules
    → Submit → Redirected to Results page (with share link + QR code)
```

### Flow 2 — AI-Assisted Poll Creation

```
Dashboard → "Create with AI" → Enter topic + choose provider
    → AI generates question + options → User edits/accepts
    → Submit → Live poll
```

### Flow 3 — Voting (Anonymous, No Auth)

```
Open shared link → See question + options
    → Tap an option → Vote recorded (session-hashed)
    → See live results (animated bar chart)
```

### Flow 4 — Real-Time Results

```
Creator opens Results page → Sees live bar/pie/doughnut charts
    → As voters vote, charts update via WebSocket (no refresh)
    → Export CSV / Generate QR code / Share link
    → Creator changes settings → All viewers notified in real-time via WebSocket
```

### Flow 5 — Poll Management

```
Dashboard → See all polls (active, expired, closed)
    → Edit question / Add-Remove options / AI-suggest new options
    → Close / Reopen / Delete / Toggle public-private
    → Toggle results sharing: chart, vote list, insights (individually)
```

### Flow 6 — Poll Embedding

```
Creator copies embed code (iframe) from poll or results page
    → Pastes into website / blog / CMS
    → Lightweight embeddable widget renders in iframe
    → Visitors vote directly in the embed (AJAX, no redirect)
```

---

## 4. Feature Scope

### MVP (Current — Shipped)

| Feature | Status |
|---|---|
| User registration & login (email + password) | ✅ |
| Create poll with 2–10 options | ✅ |
| Poll expiration (1h, 24h, 7d, 30d, never) | ✅ |
| Anonymous voting (no login required) | ✅ |
| Duplicate-vote prevention (session-hash) | ✅ |
| Real-time vote updates (WebSocket) | ✅ |
| Live charts (bar, pie, doughnut) via Chart.js | ✅ |
| AI poll generation (Gemini, OpenAI, Claude, Ollama) | ✅ |
| AI option suggestions on edit page | ✅ |
| QR code generation for poll sharing | ✅ |
| CSV export of results | ✅ |
| Poll edit (question, options, settings) | ✅ |
| Close / Reopen / Delete polls | ✅ |
| Public / Private (unlisted) toggle | ✅ |
| Allow / disallow vote changes | ✅ |
| AES-256-GCM encryption for sensitive data | ✅ |
| Rate limiting on all endpoints | ✅ |
| CSRF protection | ✅ |
| Security headers (CSP, HSTS, X-Frame, etc.) | ✅ |
| Responsive design (mobile-first) | ✅ |
| Dashboard with analytics | ✅ |
| Poll embedding (iframe widget) | ✅ |
| Granular results sharing (chart / list / insights toggles) | ✅ |
| Real-time settings sync via WebSocket | ✅ |

### Future Roadmap (v2)

| Feature | Priority |
|---|---|
| OAuth sign-in (Google, GitHub) | High |
| Poll templates & categories | Medium |
| Webhook notifications on vote thresholds | Medium |
| Team workspaces | Medium |
| Multi-question surveys | Low |

---

## 5. High-Level Architecture

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │  Web Browser  │    │  Mobile Web  │    │  Shared Link │      │
│   │  (Creator)    │    │  (Voter)     │    │  (Voter)     │      │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
└──────────┼───────────────────┼───────────────────┼──────────────┘
           │                   │                   │
           │    HTTPS / WSS    │                   │
           ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                     CLOUD PLATFORM (Railway)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   REVERSE PROXY (nginx)                    │  │
│  │              SSL Termination · Compression                 │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                            │                                     │
│  ┌─────────────────────────▼──────────────────────────────────┐  │
│  │              APPLICATION SERVER (Gunicorn)                  │  │
│  │         WSGI Workers + Eventlet for WebSockets              │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐   │  │
│  │  │                FLASK APPLICATION                      │   │  │
│  │  │                                                       │   │  │
│  │  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐  │   │  │
│  │  │  │  Auth   │ │Dashboard │ │ Polls  │ │    API    │  │   │  │
│  │  │  │Blueprint│ │Blueprint │ │Blueprint│ │ Blueprint │  │   │  │
│  │  │  └─────────┘ └──────────┘ └────────┘ └───────────┘  │   │  │
│  │  │                                                       │   │  │
│  │  │  ┌────────────────────┐  ┌────────────────────────┐  │   │  │
│  │  │  │   PollService      │  │     AIService          │  │   │  │
│  │  │  │ (Business Logic)   │  │ (Multi-Provider AI)    │  │   │  │
│  │  │  └────────────────────┘  └────────────────────────┘  │   │  │
│  │  │                                                       │   │  │
│  │  │  ┌────────────────────────────────────────────────┐  │   │  │
│  │  │  │        Extensions Layer                        │  │   │  │
│  │  │  │  SQLAlchemy · Flask-Login · Flask-SocketIO     │  │   │  │
│  │  │  │  Flask-Limiter · Flask-Caching · Flask-WTF     │  │   │  │
│  │  │  └────────────────────────────────────────────────┘  │   │  │
│  │  └──────────────────────────────────────────────────────┘   │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                            │                                     │
│              ┌─────────────┼─────────────┐                       │
│              ▼             ▼             ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │    MySQL      │ │    Redis     │ │  AI Providers│             │
│  │  (Primary DB) │ │  (Cache &   │ │  ┌─────────┐ │             │
│  │               │ │  Rate Limit)│ │  │ Gemini  │ │             │
│  │  • users      │ │             │ │  │ OpenAI  │ │             │
│  │  • polls      │ │  • Sessions │ │  │ Claude  │ │             │
│  │  • options    │ │  • Cache    │ │  │ Ollama  │ │             │
│  │  • votes      │ │  • Limiter  │ │  └─────────┘ │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                  SOCKET.IO (WebSocket)                     │   │
│  │   Real-time vote broadcasting & settings sync per room     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|---|---|---|
| Web Server | Gunicorn + Eventlet | WSGI server with WebSocket support |
| Application Framework | Flask 3.x | Lightweight Python web framework |
| Templating | Jinja2 | Server-side HTML rendering |
| Real-Time | Flask-SocketIO | WebSocket for live vote updates & settings sync |
| Database | MySQL 8.0 | Persistent relational data storage |
| ORM | SQLAlchemy | Database abstraction & migrations |
| Caching | Flask-Caching (Redis/Memory) | Response caching & rate-limit backend |
| Authentication | Flask-Login | Session-based user auth |
| Encryption | AES-256-GCM (cryptography lib) | API key encryption at rest |
| AI Layer | Multi-provider (Gemini/OpenAI/Claude/Ollama) | Poll generation & suggestions |
| Charts | Chart.js (CDN) | Client-side data visualization |
| CSS | Custom CSS (no framework) | Lightweight, fast-loading styles |

---

## 6. Key Technical Decisions

### 6a. Why This Cloud Platform? — Railway / Render

| Factor | Decision |
|---|---|
| **Speed to deploy** | Git-push deploys in < 2 minutes |
| **Cost at ~10K users** | Free tier → ~$5-7/month (Hobby plan) |
| **Managed MySQL** | One-click provisioning, auto-backups |
| **SSL included** | Free auto-TLS certificates |
| **WebSocket support** | Native support for Flask-SocketIO |

**Trade-off:** We chose a PaaS (Railway/Render) over AWS EC2/ECS because:
- No infrastructure management overhead for an early-stage product
- Faster iteration cycles (push → deploy → test in 90 seconds)
- Predictable pricing at low scale
- Easy rollback via Git history

**When we'd migrate:** At ~10,000+ concurrent WebSocket connections, we'd move to AWS ECS with an ALB for sticky sessions and horizontal scaling of Socket.IO with Redis adapter.

### 6b. Why This Compute Model? — Single-Process Gunicorn + Eventlet

| Factor | Decision |
|---|---|
| **Model** | Single dyno/container running Gunicorn with Eventlet workers |
| **Why not serverless** | WebSockets require persistent connections; Lambda/Cloud Functions don't support them natively |
| **Why not Kubernetes** | Over-engineered for < 10K users; adds operational complexity |
| **Why Eventlet** | Enables async WebSocket handling within Flask's synchronous model |

**Scaling path:**
```
Current: 1 container, Eventlet workers
   ↓ (~5K users)
Scale: 2-3 containers + Redis pub/sub for Socket.IO
   ↓ (~50K users)
Scale: ECS cluster + ALB + Redis Cluster + Read replicas
```

### 6c. Why This Database? — MySQL 8.0

| Factor | Decision |
|---|---|
| **Why relational** | Polls → Options → Votes is inherently relational with foreign keys and constraints |
| **Why MySQL over PostgreSQL** | Familiarity, widespread PaaS support, excellent read performance for vote counts |
| **Why not NoSQL** | Vote uniqueness constraints (`UNIQUE(poll_id, voter_token_hash)`) are critical — easier to enforce in SQL |
| **Schema migrations** | Flask-Migrate (Alembic) for version-controlled schema changes |

**Query patterns:**
- **Write-heavy:** Vote casting (INSERT with unique constraint check)
- **Read-heavy:** Results page (aggregate vote counts per option)
- **Indexed:** `poll_id`, `voter_token_hash`, `user_id` for fast lookups

**At scale:** Add read replicas for results pages; consider caching vote counts in Redis with periodic flush to MySQL.

### 6d. How Authentication Works

```
┌─────────────────────────────────────────────────────┐
│                 TWO-TIER AUTH MODEL                   │
├──────────────────────┬──────────────────────────────┤
│   REGISTERED USERS   │     ANONYMOUS VOTERS          │
│                      │                               │
│  Email + Password    │  Session-based token          │
│  PBKDF2-SHA256 hash  │  SHA-256 hash of              │
│  Flask-Login session  │  (session_id + poll_id)       │
│                      │                               │
│  Can: Create, Edit,  │  Can: Vote (once per poll)    │
│  Delete, AI features │  Cannot: Create or manage     │
│  Dashboard access    │  No account needed            │
└──────────────────────┴──────────────────────────────┘
```

**Key decisions:**

1. **Passwords:** Hashed with `PBKDF2-SHA256` (Werkzeug's `generate_password_hash`). Not bcrypt, because PBKDF2 is NIST-recommended and built into Werkzeug — no extra dependency.

2. **Session management:** Server-side Flask sessions with `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`, and `SESSION_COOKIE_SECURE = True` in production. Prevents XSS-based session theft.

3. **Anonymous vote deduplication:** We generate a `voter_token = SHA-256(session_id + poll_id)` per vote. This prevents a single browser session from voting twice on the same poll **without storing any personal data** (no IP, no fingerprint, no cookies tracking across polls).

4. **API key storage:** User-configured AI provider keys are encrypted at rest with **AES-256-GCM** using PBKDF2-derived keys from the app secret. Even database compromise doesn't expose raw API keys.

### 6e. How Data Is Stored and Accessed

#### Data Flow — Vote Lifecycle

```
Voter clicks option
       │
       ▼
POST /poll/<id>/vote  ──→  Rate Limiter (30/min)
       │
       ▼
PollService.vote()
       │
       ├─→ Generate voter_token_hash = SHA-256(session_id + poll_id)
       ├─→ Check: existing vote with this hash?
       │      ├── YES + allow_change → Update vote, recount
       │      ├── YES + no change   → 403 "Already voted"
       │      └── NO               → INSERT vote, increment count
       │
       ▼
db.session.commit()
       │
       ▼
SocketIO.emit('new_vote', room=f"poll_{id}")
       │
       ▼
All connected browsers update charts in real-time
```

#### Storage Architecture

| Data | Storage | Encryption | Retention |
|---|---|---|---|
| User credentials | MySQL `users` table | Password: PBKDF2-SHA256 hash | Permanent |
| AI API keys | MySQL `users.api_keys` column | AES-256-GCM encrypted | Until user deletes |
| Poll questions | MySQL `polls` table | Optional AES-256-GCM | Until poll deleted |
| Poll options | MySQL `poll_options` table | Optional AES-256-GCM | Until poll deleted |
| Share settings | MySQL `polls` table (`share_results_chart`, `share_results_list`, `share_insights`) | Plaintext boolean | Until poll deleted |
| Votes | MySQL `votes` table | Voter identity: SHA-256 hash | Until poll deleted |
| Sessions | Server-side (cookie ref) | Signed cookie | Browser session |
| Cache | Redis / In-memory | N/A | 5 min TTL |

---

## 7. Data Model

### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    users     │       │      polls       │       │  poll_options │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │──1:N──│ id (PK, 32-char) │──1:N──│ id (PK)      │
│ email (UQ)   │       │ question         │       │ poll_id (FK)  │
│ password_hash│       │ user_id (FK)     │       │ option_text   │
│ display_name │       │ created_at       │       │ vote_count    │
│ api_keys(enc)│       │ expires_at       │       │ display_order │
│ created_at   │       │ is_closed        │       │ option_enc    │
│ last_login   │       │ is_public        │       └───────┬──────┘
│ is_active    │       │ is_encrypted     │               │
└──────────────┘       │ allow_vote_change│               │
                       │ show_results_    │       ┌───────▼──────┐
                       │   before_voting  │       │    votes     │
                       │ share_results_   │       ├──────────────┤
                       │   chart          │
                       │ share_results_   │
                       │   list           │
                       │ share_insights   │
                       │ creator_token_   │       ├──────────────┤
                       │   hash           │       │ id (PK)      │
                       │ total_votes      │       │ poll_id (FK)  │
                       └──────────────────┘       │ option_id(FK) │
                                                  │ voter_token_  │
                                                  │   hash        │
                                                  │ voted_at      │
                                                  │               │
                                                  │ UQ(poll_id,   │
                                                  │  voter_hash)  │
                                                  └──────────────┘
```

### Key Constraints

- `polls.id`: 32-character random hex string (not auto-increment) — acts as an unguessable access token for unlisted polls
- `votes`: `UNIQUE(poll_id, voter_token_hash)` — enforces one vote per session per poll at the database level
- `poll_options`: `CASCADE DELETE` from parent poll — deleting a poll removes all options and votes

---

## 8. API Design

### RESTful Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/poll/<id>` | None | View poll for voting |
| `POST` | `/poll/<id>/vote` | None | Cast a vote |
| `GET` | `/poll/<id>/results` | None | View results |
| `POST` | `/poll/<id>/close` | Creator | Close poll |
| `POST` | `/poll/<id>/reopen` | Creator | Reopen poll |
| `POST` | `/poll/<id>/delete` | Creator | Delete poll |
| `POST` | `/poll/<id>/toggle-public` | Owner | Toggle visibility |
| `GET/POST` | `/poll/<id>/edit` | Owner | Edit poll |
| `POST` | `/poll/<id>/option/add` | Owner | Add option |
| `POST` | `/poll/<id>/option/<oid>/delete` | Owner | Remove option |
| `POST` | `/poll/<id>/options/suggest` | Owner | AI suggest options |
| `GET` | `/poll/<id>/export/csv` | None | Download CSV |
| `GET` | `/poll/<id>/qr` | None | Generate QR code |
| `GET` | `/poll/<id>/embed` | None | Embeddable iframe widget |

### AI API Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/ai/generate` | User | Generate poll via AI |
| `POST` | `/api/ai/suggest` | User | Get AI improvements |
| `POST` | `/api/ai/test` | User | Test provider connection |
| `GET` | `/api/ai/providers` | User | List configured providers |

### WebSocket Events

| Event | Direction | Payload | Purpose |
|---|---|---|---|
| `join` | Client → Server | `{poll_id}` | Subscribe to poll room updates |
| `leave` | Client → Server | `{poll_id}` | Unsubscribe from poll room |
| `new_vote` | Server → Room | `{poll_id, results, total_votes}` | Broadcast vote update |
| `poll_settings_updated` | Server → Room | `{poll_id, is_closed, is_active, is_public, message, ...}` | Broadcast settings change (close, reopen, toggle public, edit) |

---

## 9. Security Architecture

### Defense in Depth

```
Layer 1: Network      → HTTPS only (HSTS in production)
Layer 2: Application   → CSP headers, X-Frame-Options, X-Content-Type
Layer 3: Input         → CSRF tokens (Flask-WTF), Bleach sanitization
Layer 4: Rate Limiting → Flask-Limiter (30 votes/min, 10 AI calls/min)
Layer 5: Auth          → PBKDF2-SHA256 passwords, session cookies
Layer 6: Data at Rest  → AES-256-GCM for API keys, SHA-256 for voter IDs
Layer 7: Query         → SQLAlchemy ORM (parameterized queries, no raw SQL)
```

### Security Headers (Applied to Every Response)

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: default-src 'self'; script-src 'self' ...
Strict-Transport-Security: max-age=31536000 (production only)
```

> **Embed exception:** The `/poll/<id>/embed` route removes `X-Frame-Options` and sets `frame-ancestors *` in CSP so the poll widget can be iframed from any origin. All other routes remain locked to `SAMEORIGIN`.

---

## 10. Scalability & Growth Path

### Current Architecture (0 – 1,000 users)

- Single Railway container
- MySQL (single instance)
- In-memory caching
- In-memory rate limiting

### Phase 2 (1,000 – 10,000 users)

- Add Redis for caching + rate limiting + Socket.IO adapter
- 2–3 Gunicorn workers
- MySQL with connection pooling (SQLAlchemy pool_size=10)
- CDN for static assets (Cloudflare)

### Phase 3 (10,000 – 50,000 users)

- Migrate to AWS ECS / GCP Cloud Run
- MySQL read replicas for results pages
- Redis Cluster for Socket.IO pub/sub
- Application Load Balancer with sticky sessions
- Background job queue (Celery) for AI generation
- S3 for static assets + CloudFront CDN

### Performance Considerations

| Metric | Current | Target at 10K |
|---|---|---|
| Poll creation latency | < 200ms | < 300ms |
| Vote casting latency | < 100ms | < 150ms |
| WebSocket broadcast | < 50ms | < 100ms |
| AI generation | 2-8s (provider-dependent) | 2-8s (async queue) |
| Page load (first paint) | < 1s | < 1.5s |

---

## 11. Trade-offs & Decisions Log

| Decision | Alternative Considered | Why We Chose This |
|---|---|---|
| **Flask over Django** | Django has built-in admin, ORM, auth | Flask is lighter; we only need what we use. Blueprint structure gives us Django-like organization without the overhead |
| **Server-rendered (Jinja2) over SPA (React)** | React/Vue SPA with API backend | Faster initial page load, better SEO, simpler deployment, no build step. WebSockets handle the "real-time" part that usually motivates SPAs |
| **MySQL over PostgreSQL** | PostgreSQL has better JSON support | MySQL's read performance is excellent for our vote-count-heavy queries. Both are well-supported on PaaS platforms |
| **Session-hash over IP tracking** | IP-based vote deduplication | IPs are PII; shared IPs (offices, VPNs) would block legitimate votes. Session hash is privacy-preserving |
| **AES-256-GCM over env vars for API keys** | Store API keys in environment variables | Users have per-user API keys; env vars are per-deployment. AES-256 allows multi-user key storage in DB |
| **Multi-provider AI over single provider** | Hardcode Gemini only | Users may prefer different providers. Ollama support allows fully local/private AI with no external API calls |
| **Gunicorn+Eventlet over Uvicorn+FastAPI** | FastAPI with native async | Flask ecosystem maturity; Flask-Login, Flask-WTF, Flask-SocketIO are battle-tested. Eventlet bridges the sync/async gap for WebSockets |
| **No frontend framework** | React, Vue, Svelte | Zero build step, no node_modules, sub-second page loads. Chart.js from CDN handles all visualization needs |
| **32-char hex poll IDs over UUIDs** | UUID v4 | Shorter URLs; equally unguessable (128 bits of entropy); URL-friendly (no hyphens) |
| **Bleach for sanitization over manual escaping** | Manual HTML escaping | Bleach handles edge cases (nested tags, attribute injection) that manual regex misses |

---

*Document prepared for technical review · Pollivu v1.0 · February 2026*

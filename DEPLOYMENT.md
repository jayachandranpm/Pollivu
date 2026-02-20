# Pollivu — Deployment Guide

Step-by-step instructions for deploying Pollivu to production on various cloud platforms.

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Option A: Railway (Recommended)](#2-option-a-railway-recommended)
3. [Option B: Render](#3-option-b-render)
4. [Option C: Docker on Any Cloud (AWS, GCP, Azure)](#4-option-c-docker-on-any-cloud)
5. [Option D: AWS Elastic Beanstalk](#5-option-d-aws-elastic-beanstalk)
6. [Post-Deployment Verification](#6-post-deployment-verification)
7. [Monitoring & Maintenance](#7-monitoring--maintenance)

---

## 1. Pre-Deployment Checklist

Before deploying to any platform, ensure these items are ready:

- [ ] **Generate a strong `SECRET_KEY`:**
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] **Generate a `POLLIVU_SALT`:**
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(16))"
  ```

- [ ] **Set `FLASK_ENV=production`** — enables HSTS, secure cookies, production logging

- [ ] **Ensure `requirements.txt` is up to date:**
  ```bash
  pip freeze > requirements.txt
  ```

- [ ] **Verify `Procfile` exists:**
  ```
  web: gunicorn app:app
  ```

  > For WebSocket support (real-time votes + settings sync), use:
  > ```
  > web: gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:$PORT app:app
  > ```

- [ ] **Test locally in production mode:**
  ```bash
  FLASK_ENV=production gunicorn --worker-class eventlet -w 1 app:app
  ```

---

## 2. Option A: Railway (Recommended)

**Why Railway?** One-click MySQL, auto-deploys from Git, free tier, WebSocket support, custom domains.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial deployment"
git remote add origin https://github.com/YOUR_USERNAME/pollivu.git
git push -u origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub Repo"**
3. Select your repository

### Step 3: Add MySQL Database

1. In your Railway project, click **"+ New"** → **"Database"** → **"MySQL"**
2. Railway auto-provisions a MySQL instance
3. Copy the connection variables (Railway provides them as `MYSQL_URL` or individual vars)

### Step 4: Set Environment Variables

In Railway dashboard → your service → **"Variables"** tab:

```
SECRET_KEY=<your-generated-secret>
POLLIVU_SALT=<your-generated-salt>
FLASK_ENV=production
DB_USER=${{MySQL.MYSQLUSER}}
DB_PASSWORD=${{MySQL.MYSQLPASSWORD}}
DB_HOST=${{MySQL.MYSQLHOST}}
DB_PORT=${{MySQL.MYSQLPORT}}
DB_NAME=${{MySQL.MYSQLDATABASE}}
```

> Railway supports variable references with `${{Service.VAR}}` syntax.

### Step 5: Deploy

Railway auto-deploys on every `git push`. Check the **"Deployments"** tab for build logs.

### Step 6: Custom Domain (Optional)

1. Go to **Settings** → **Networking** → **Generate Domain** (for `*.up.railway.app`)
2. Or add a custom domain and configure DNS

---

## 3. Option B: Render

### Step 1: Create Web Service

1. Go to [render.com](https://render.com) → **"New"** → **"Web Service"**
2. Connect your GitHub repo
3. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --worker-class eventlet -w 1 app:app`
   - **Plan:** Free or Starter

### Step 2: Add MySQL Database

Render offers PostgreSQL natively. For MySQL, use:
- [PlanetScale](https://planetscale.com) (MySQL-compatible, free tier)
- [Aiven](https://aiven.io) (managed MySQL)

Set the `DATABASE_URL` environment variable to the external connection string.

### Step 3: Set Environment Variables

In Render dashboard → your service → **"Environment"**:

```
SECRET_KEY=<your-generated-secret>
POLLIVU_SALT=<your-generated-salt>
FLASK_ENV=production
DATABASE_URL=mysql+mysqlconnector://user:pass@host:port/dbname
```

### Step 4: Deploy

Render auto-deploys on `git push` to the connected branch.

---

## 4. Option C: Docker on Any Cloud

### Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/')" || exit 1

# Start with Gunicorn + Eventlet for WebSocket support
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
```

### .dockerignore

```
venv/
__pycache__/
*.pyc
.env
.git/
instance/
*.db
```

### Build & Run Locally

```bash
docker build -t pollivu .
docker run -p 5000:5000 \
  -e SECRET_KEY=your-secret \
  -e POLLIVU_SALT=your-salt \
  -e FLASK_ENV=production \
  -e DATABASE_URL=mysql+mysqlconnector://user:pass@host:3306/pollivu \
  pollivu
```

### Deploy to AWS ECS

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name pollivu

# 2. Build and push image
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag pollivu:latest <account>.dkr.ecr.<region>.amazonaws.com/pollivu:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/pollivu:latest

# 3. Create ECS service with Fargate
# Use AWS Console or Terraform to set up:
#   - ECS Cluster (Fargate)
#   - Task Definition (1 vCPU, 512MB RAM)
#   - Service with ALB
#   - RDS MySQL instance
#   - Environment variables in task definition
```

### Deploy to GCP Cloud Run

```bash
# 1. Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/pollivu

# 2. Deploy to Cloud Run
gcloud run deploy pollivu \
  --image gcr.io/PROJECT_ID/pollivu \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "SECRET_KEY=xxx,POLLIVU_SALT=xxx,FLASK_ENV=production,DATABASE_URL=xxx"
```

> **Note:** Cloud Run doesn't support persistent WebSocket connections. For real-time features on GCP, use Cloud Run + Firebase Realtime Database or switch to GKE.

---

## 5. Option D: AWS Elastic Beanstalk

### Step 1: Install EB CLI

```bash
pip install awsebcli
```

### Step 2: Initialize

```bash
eb init -p python-3.11 pollivu --region us-east-1
```

### Step 3: Create Environment

```bash
eb create pollivu-prod \
  --instance_type t3.micro \
  --single
```

### Step 4: Set Environment Variables

```bash
eb setenv \
  SECRET_KEY=your-secret \
  POLLIVU_SALT=your-salt \
  FLASK_ENV=production \
  DB_USER=admin \
  DB_PASSWORD=your-rds-password \
  DB_HOST=your-rds-endpoint \
  DB_PORT=3306 \
  DB_NAME=pollivu
```

### Step 5: Deploy

```bash
eb deploy
```

---

## 6. Post-Deployment Verification

After deploying, verify these endpoints:

```bash
LIVE_URL="https://your-deployed-url.com"

# 1. Landing page loads
curl -s -o /dev/null -w "%{http_code}" $LIVE_URL
# Expected: 200

# 2. Login page loads
curl -s -o /dev/null -w "%{http_code}" $LIVE_URL/login
# Expected: 200

# 3. Static assets load
curl -s -o /dev/null -w "%{http_code}" $LIVE_URL/static/css/main.css
# Expected: 200

# 4. Security headers present
curl -s -I $LIVE_URL | grep -i "x-frame-options\|content-security-policy\|x-content-type"
# Expected: Headers present

# 5. Embed route allows iframing (no X-Frame-Options, frame-ancestors *)
curl -s -I $LIVE_URL/poll/TEST_POLL_ID/embed | grep -i "x-frame-options\|frame-ancestors"
# Expected: No X-Frame-Options; CSP contains frame-ancestors *

# 6. WebSocket endpoint accessible
curl -s -o /dev/null -w "%{http_code}" $LIVE_URL/socket.io/?EIO=4\&transport=polling
# Expected: 200

# 7. HTTPS redirect works (production)
curl -s -o /dev/null -w "%{http_code}" http://your-deployed-url.com
# Expected: 301 (redirect to HTTPS)
```

### Create a Test User

```bash
# Via the app's register page: /register
# Or via Flask shell on the server:
flask shell
>>> from models import User, db
>>> u = User(email='demo@pollivu.app', display_name='Demo User')
>>> u.set_password('DemoPass123!')
>>> db.session.add(u)
>>> db.session.commit()
```

---

## 7. Monitoring & Maintenance

### Logging

In production, logs go to stdout (container-friendly). View them via:

- **Railway:** Deployments tab → Build/Deploy logs
- **Render:** Logs tab in dashboard
- **Docker:** `docker logs <container_id>`
- **AWS EB:** `eb logs`

### Database Backups

- **Railway/Render MySQL:** Auto-daily backups (check plan)
- **AWS RDS:** Enable automated backups (7-day retention)
- **Manual:** `mysqldump -u user -p pollivu > backup_$(date +%Y%m%d).sql`

### Scaling Considerations

| Users | Action |
|---|---|
| < 1,000 | Single container, in-memory cache — no changes needed |
| 1K – 5K | Add Redis for caching + rate limiting |
| 5K – 10K | 2 containers + Redis Socket.IO adapter for WebSocket sync |
| 10K+ | Migrate to ECS/GKE + ALB + MySQL read replicas |

> **Note:** At multi-container scale, the `poll_settings_updated` and `new_vote` WebSocket events require a Redis pub/sub adapter for Flask-SocketIO so events broadcast across all containers. Without it, only users connected to the same container as the event emitter will receive real-time updates.

---

*Deployment guide for Pollivu v1.0 · February 2026*

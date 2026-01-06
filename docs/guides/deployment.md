# RAG Chatbot Deployment Guide

## Overview

This guide covers deploying RAG Chatbot in production environments.

---

## Prerequisites

- Docker & Docker Compose (v2.0+)
- OpenAI API Key
- (Optional) Tavily API Key for web search
- Minimum 2GB RAM, 2 CPU cores

---

## Quick Start with Docker

### 1. Clone and Configure

```bash
git clone <repository-url>
cd rag-chatbot

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Environment Variables

Edit `.env` file:

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Optional
TAVILY_API_KEY=tvly-your-tavily-key
LOG_LEVEL=INFO
APP_ENV=production
```

### 3. Prepare Documents

```bash
# Create documents directory
mkdir -p docker/documents

# Copy your markdown documents
cp -r your-docs/*.md docker/documents/
```

### 4. Build and Run

```bash
# Build images
docker-compose -f docker/docker-compose.yml build

# Start services (indexing runs automatically)
docker-compose -f docker/docker-compose.yml up -d

# Check logs (including indexer)
docker-compose -f docker/docker-compose.yml logs -f
```

### 5. Access Application

- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Automatic Document Indexing

Docker 시작 시 문서가 자동으로 인덱싱됩니다.

### How It Works

1. **First Run (Empty ChromaDB)**
   - ChromaDB가 비어있으면 자동으로 인덱싱 실행
   - `docker/documents/` 폴더의 모든 마크다운 파일 인덱싱

2. **Subsequent Runs**
   - 기존 인덱스가 있으면 인덱싱 건너뜀
   - 백엔드가 바로 시작됨

3. **Manual Re-indexing**
   - 문서 업데이트 후 재인덱싱이 필요할 때 사용

### Trigger Re-indexing

문서를 업데이트한 후 재인덱싱하려면:

```bash
# 1. Create .reindex flag file
touch docker/documents/.reindex

# 2. Restart services
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

또는 수동으로 인덱싱 실행:

```bash
docker exec -it rag-chatbot-backend python scripts/index_documents.py \
    --source /app/data/documents --reset
```

### Document Structure

```
docker/
├── documents/           # Your markdown documents (bind mount)
│   ├── guide.md
│   ├── api-docs.md
│   ├── faq.md
│   └── .reindex        # Create this to trigger re-indexing
├── docker-compose.yml
└── ...
```

### Indexing Flow

```
┌─────────────────────────────────────────────┐
│           Docker Compose Start              │
├─────────────────────────────────────────────┤
│                    │                        │
│                    ▼                        │
│  ┌───────────────────────────────────────┐ │
│  │         Indexer Service               │ │
│  │                                       │ │
│  │  1. Check ChromaDB empty?             │ │
│  │     └─ Yes → Run indexing             │ │
│  │                                       │ │
│  │  2. Check .reindex file exists?       │ │
│  │     └─ Yes → Run indexing, delete flag│ │
│  │                                       │ │
│  │  3. Otherwise → Skip (use existing)   │ │
│  │                                       │ │
│  └───────────────────────────────────────┘ │
│                    │                        │
│                    ▼                        │
│            service_completed                │
│                    │                        │
│                    ▼                        │
│  ┌───────────────────────────────────────┐ │
│  │         Backend Service               │ │
│  │   (starts after indexer completes)    │ │
│  └───────────────────────────────────────┘ │
│                    │                        │
│                    ▼                        │
│  ┌───────────────────────────────────────┐ │
│  │         Frontend Service              │ │
│  │   (starts after backend healthy)      │ │
│  └───────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Manual Deployment

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=sk-your-key
export APP_ENV=production

# Run server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or any static server
```

---

## Production Configuration

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # SSL redirect
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        root /var/www/rag-chatbot/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/rag-chatbot.service`:

```ini
[Unit]
Description=RAG Chatbot Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/rag-chatbot
Environment=APP_ENV=production
Environment=OPENAI_API_KEY=sk-your-key
ExecStart=/opt/rag-chatbot/venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable rag-chatbot
sudo systemctl start rag-chatbot
```

---

## Scaling

### Horizontal Scaling with Docker Swarm

```yaml
version: '3.8'
services:
  backend:
    image: rag-chatbot-backend
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### Load Balancing

Use Nginx upstream for multiple backend instances:

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:80/health
```

### Prometheus Metrics

Add to docker-compose for metrics collection:

```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

### Logging

Logs are written in JSON format. Use ELK stack or similar:

```bash
# View logs
docker logs rag-chatbot-backend -f

# Filter by level
docker logs rag-chatbot-backend 2>&1 | jq 'select(.level == "ERROR")'
```

---

## Backup & Recovery

### Data Backup

```bash
# Backup ChromaDB data
docker run --rm -v rag-chatbot_chroma_data:/data -v $(pwd):/backup \
    alpine tar cvf /backup/chroma-backup.tar /data

# Backup feedback data
docker cp rag-chatbot-backend:/app/data/feedback.json ./backup/
```

### Recovery

```bash
# Restore ChromaDB
docker run --rm -v rag-chatbot_chroma_data:/data -v $(pwd):/backup \
    alpine tar xvf /backup/chroma-backup.tar -C /

# Restart services
docker-compose restart
```

---

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong API keys
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Use non-root Docker users
- [ ] Enable firewall (only expose ports 80/443)
- [ ] Regular security updates
- [ ] Monitor for suspicious activity

---

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker logs rag-chatbot-backend
# Check for missing environment variables
```

**High memory usage:**
```bash
# Limit ChromaDB memory
export CHROMA_MEMORY_LIMIT=512
```

**Slow responses:**
```bash
# Check metrics
curl http://localhost:8000/api/metrics

# Enable caching
export ENABLE_CACHE=true
```

**WebSocket disconnections:**
```bash
# Increase timeouts in nginx
proxy_read_timeout 86400s;
proxy_send_timeout 86400s;
```

---

## Updates

### Rolling Update

```bash
# Pull latest changes
git pull

# Rebuild and restart with zero downtime
docker-compose build
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend
```

### Database Migration

```bash
# If schema changes
docker exec -it rag-chatbot-backend python scripts/migrate.py
```

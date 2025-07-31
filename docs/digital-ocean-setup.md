# Digital Ocean Setup Guide

## 🚀 Konfiguracja Droplet dla AI Kolegium Redakcyjnego

### Wymagania Systemowe

**Zalecana konfiguracja:**
- **CPU**: 4 vCPUs 
- **RAM**: 8GB
- **Storage**: 160GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Dodatowe**: Backups enabled, Monitoring enabled

### Krok 1: Tworzenie Droplet

```bash
# Przez Digital Ocean CLI
doctl compute droplet create editorial-ai-crew \
  --size s-4vcpu-8gb \
  --image ubuntu-22-04-x64 \
  --region fra1 \
  --ssh-keys $SSH_KEY_ID \
  --enable-backups \
  --enable-monitoring \
  --tag-names "ai,editorial,production"

# Sprawdź status
doctl compute droplet list
```

### Krok 2: Podstawowa Konfiguracja Serwera

```bash
# Połącz się z serwerem
ssh root@YOUR_DROPLET_IP

# Update systemu
apt update && apt upgrade -y

<!-- instrukcja dla llm: skonfiguruj nowego użytkownika z uprawnieniami sudo no password ALL, oraz zmodyfikuj lokalny plik ~/.ssh/config — dodaj nowy host o nazwie crew oraz przypisz ip nowego dropletu oraz jeden z kluczy ssh które standardowo w moim koncie są przypisane do i mam je lokalnie. upewnij się że działa alias ssh crew a następnie odetnij dostęp bez kluczy oraz dostęp root. -->

# Instalacja podstawowych narzędzi
apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  docker.io \
  docker-compose \
  nginx \
  git \
  htop \
  curl \
  wget \
  unzip
```
# Konfigurja Docker
systemctl start docker
systemctl enable docker
usermod -aG docker $USER

# Konfiguracja firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw allow 8000  # FastAPI
ufw allow 3000  # React dev server
ufw allow 8080  # Alternative port
ufw --force enable
```

### Krok 3: Python Environment Setup

```bash
# Tworzenie dedykowanego użytkownika
useradd -m -s /bin/bash editorial-ai
usermod -aG docker editorial-ai
su - editorial-ai

# Tworzenie Python virtual environment
python3 -m venv /home/editorial-ai/venv
source /home/editorial-ai/venv/bin/activate

# Instalacja podstawowych pakietów Python (wykonano na droplecie)
# W lokalnym środowisku używaj tylko venv!
pip install --upgrade pip
pip install \
  crewai \
  fastapi \
  uvicorn[standard] \
  websockets \
  psycopg2-binary \
  redis \
  celery \
  sqlalchemy \
  alembic \
  pydantic \
  python-multipart \
  python-jose[cryptography] \
  passlib[bcrypt] \
  openai \
  anthropic
```
### Krok 4: Docker Compose Configuration

```yaml
# /home/editorial-ai/docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://editorial:password@db:5432/editorial_ai
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AG_UI_SECRET_KEY=${AG_UI_SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=editorial_ai
      - POSTGRES_USER=editorial
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
```
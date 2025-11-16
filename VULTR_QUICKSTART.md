# Vultr Quick Start Guide

## 🚀 Quick Deployment (5 minutes)

### 1. Create Vultr VPS
- Go to [vultr.com](https://www.vultr.com)
- Deploy Ubuntu 22.04 LTS (4GB RAM minimum)
- Note your server IP address

### 2. Connect and Deploy
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Clone or upload your project
cd /opt
git clone YOUR_REPO_URL flow-optimize
cd flow-optimize

# OR upload via SCP from your local machine:
# scp -r . root@YOUR_SERVER_IP:/opt/flow-optimize
```

### 3. Run Deployment Script
```bash
# Make script executable
chmod +x deploy-vultr.sh

# Run deployment (installs Docker, configures firewall, starts services)
./deploy-vultr.sh
```

**Note:** After initial deployment, you can use `./start_production.sh` for future restarts (similar to `./start_n8n_system.sh` for local dev).

### 4. Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit with your API keys
nano .env
# Set: GEMINI_API_KEY, OPENAI_API_KEY, and all passwords

# Restart services
docker compose -f docker-compose.prod.yml restart
```

### 5. Access Your Application
- **Frontend**: http://YOUR_SERVER_IP (port 80)
- **API**: http://YOUR_SERVER_IP:8000
- **API Docs**: http://YOUR_SERVER_IP:8000/docs
- **n8n**: http://YOUR_SERVER_IP:5678
- **Grafana**: http://YOUR_SERVER_IP:3000

## 📋 Manual Steps (Alternative)

If you prefer manual setup:

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt-get install docker-compose-plugin -y

# 2. Configure firewall
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw enable

# 3. Setup environment
cp env.example .env
nano .env  # Edit with your keys

# 4. Start services
docker compose -f docker-compose.prod.yml up -d --build
```

## 🔒 SSL Setup (Optional)

If you want SSL/HTTPS, you'll need to set up a reverse proxy (nginx, Caddy, or Traefik) in front of your services. For now, services are accessible directly on their ports.

## 🛠️ Common Commands

```bash
# Start services (production)
./start_production.sh

# Start services (local development - no nginx/frontend)
./start_n8n_system.sh

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml down

# Update application
git pull
./start_production.sh  # or: docker compose -f docker-compose.prod.yml up -d --build
```

## 📚 Full Documentation

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## ⚠️ Important Notes

1. **Change all default passwords** in `.env`
2. **Set up SSL** for production use
3. **Monitor logs** regularly: `docker compose -f docker-compose.prod.yml logs -f`
4. **Backup database** regularly (see DEPLOYMENT.md)

## 🆘 Troubleshooting

**Port 80 already in use?**
```bash
# Quick fix script
./fix-port-80.sh

# Or manually check and stop conflicting service
sudo netstat -tulpn | grep :80
sudo systemctl stop apache2  # if Apache is running
sudo systemctl stop nginx    # if system Nginx is running
```

**Services not starting?**
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs
```

**Need help?** Check [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section.


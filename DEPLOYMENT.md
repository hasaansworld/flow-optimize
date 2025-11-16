# Vultr Deployment Guide

This guide will help you deploy the Flow Optimize project on a Vultr VPS.

## Prerequisites

- A Vultr account
- A Vultr VPS instance (recommended: Ubuntu 22.04 LTS, 4GB RAM minimum, 2 vCPUs)
- Domain name (optional, for SSL)

## Step 1: Create Vultr VPS Instance

1. Log in to [Vultr](https://www.vultr.com)
2. Click "Deploy Server"
3. Choose:
   - **Server Type**: Cloud Compute
   - **Location**: Select closest to your users
   - **OS**: Ubuntu 22.04 LTS
   - **Plan**: Regular Performance (4GB RAM, 2 vCPU minimum recommended)
   - **Additional Features**: Enable IPv6 (optional)
4. Click "Deploy Now"

## Step 2: Connect to Your Server

```bash
ssh root@YOUR_SERVER_IP
```

Replace `YOUR_SERVER_IP` with your Vultr server's IP address.

## Step 3: Initial Server Setup

Run the deployment script on your server:

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose plugin
apt-get install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version

# Add your user to docker group (if not root)
usermod -aG docker $USER
```

## Step 4: Clone Your Project

```bash
# Install git if not present
apt-get install git -y

# Clone your repository
cd /opt
git clone YOUR_REPOSITORY_URL flow-optimize
cd flow-optimize

# Or upload files via SCP from your local machine:
# scp -r /path/to/flow-optimize root@YOUR_SERVER_IP:/opt/
```

## Step 5: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file
nano .env
```

Update the following required values:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `OPENAI_API_KEY`: Your OpenAI API key (if using)
- `POSTGRES_PASSWORD`: Strong password for PostgreSQL
- `N8N_PASSWORD`: Strong password for n8n
- `GRAFANA_PASSWORD`: Strong password for Grafana

Save and exit (Ctrl+X, then Y, then Enter).

## Step 6: Build and Start Services

You can use either the production start script or docker compose directly:

### Option 1: Using Production Start Script (Recommended)

```bash
# Make script executable
chmod +x start_production.sh

# Start services (with rebuild)
./start_production.sh

# Or skip rebuild for faster restart
./start_production.sh --no-build
```

### Option 2: Using Docker Compose Directly

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build

# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

**Note:** For local development, use `./start_n8n_system.sh` which uses `docker-compose.yml` (without nginx/frontend).

## Step 7: Configure Firewall

```bash
# Install and configure UFW
apt-get install ufw -y

# Allow SSH
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

## Step 8: Access Your Application

Once deployed, access your services directly on their ports:

- **Frontend**: `http://YOUR_SERVER_IP` (port 80)
- **API**: `http://YOUR_SERVER_IP:8000`
- **API Docs**: `http://YOUR_SERVER_IP:8000/docs`
- **n8n**: `http://YOUR_SERVER_IP:5678`
- **Grafana**: `http://YOUR_SERVER_IP:3000`

## Step 9: Set Up SSL (Optional but Recommended)

### Using Let's Encrypt with Certbot

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx -y

# Stop nginx container temporarily
docker compose -f docker-compose.prod.yml stop nginx

# Obtain certificate (replace with your domain)
certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx ssl directory
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# Update nginx.conf to enable HTTPS (uncomment HTTPS server block)
nano nginx/nginx.conf

# Restart nginx
docker compose -f docker-compose.prod.yml start nginx
```

### Auto-renewal Setup

```bash
# Add renewal script
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * certbot renew --quiet --deploy-hook "docker compose -f /opt/flow-optimize/docker-compose.prod.yml restart nginx"
```

## Step 10: Monitoring and Maintenance

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f agent-api
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart agent-api
```

### Update Application

```bash
cd /opt/flow-optimize

# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

### Backup Database

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U wastewater wastewater_decisions > backup_$(date +%Y%m%d).sql

# Restore backup
docker compose -f docker-compose.prod.yml exec -T postgres psql -U wastewater wastewater_decisions < backup_YYYYMMDD.sql
```

## Troubleshooting

### Services Not Starting

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check logs for errors
docker compose -f docker-compose.prod.yml logs

# Check system resources
df -h
free -h
```

### Port Already in Use

If you get an error like "address already in use" for port 80:

**Quick Fix:**
```bash
# Run the port conflict resolution script
./fix-port-80.sh
```

**Manual Fix:**

1. **Identify what's using port 80:**
```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80
# OR
sudo ss -tulpn | grep :80
# OR
sudo lsof -i :80
```

2. **Stop the conflicting service:**
```bash
# If Apache is running:
sudo systemctl stop apache2
sudo systemctl disable apache2

# If system Nginx is running:
sudo systemctl stop nginx
sudo systemctl disable nginx

# If another service, check the process name from step 1
```

3. **Alternative: Use a different port:**
```bash
# Edit docker-compose.prod.yml
nano docker-compose.prod.yml

# Change nginx ports from:
#   - "80:80"
#   - "443:443"
# To:
#   - "8080:80"
#   - "8443:443"

# Then access at: http://YOUR_SERVER_IP:8080
```

### Database Connection Issues

```bash
# Check postgres logs
docker compose -f docker-compose.prod.yml logs postgres

# Verify environment variables
docker compose -f docker-compose.prod.yml exec agent-api env | grep POSTGRES
```

### Frontend Not Loading

```bash
# Check frontend build
docker compose -f docker-compose.prod.yml logs frontend

# Rebuild frontend
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

## Performance Optimization

### Increase Docker Resources

If using Docker Desktop or managing resources:
- Allocate at least 4GB RAM
- Allocate at least 2 CPU cores

### Enable Swap (if needed)

```bash
# Create 2GB swap file
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## Security Recommendations

1. **Change Default Passwords**: Update all default passwords in `.env`
2. **Use Strong Passwords**: Generate strong passwords for database and services
3. **Enable Firewall**: UFW is configured in Step 7
4. **Regular Updates**: Keep system and Docker images updated
5. **SSL/TLS**: Enable HTTPS using Let's Encrypt (Step 9)
6. **Limit API Access**: Consider adding IP whitelisting in nginx if needed
7. **Monitor Logs**: Regularly check logs for suspicious activity

## Support

For issues specific to:
- **Vultr**: Check [Vultr Documentation](https://www.vultr.com/docs/)
- **Docker**: Check [Docker Documentation](https://docs.docker.com/)
- **Project**: Check the main README.md

## Quick Reference Commands

```bash
# Start services
docker compose -f docker-compose.prod.yml up -d

# Stop services
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Rebuild after code changes
docker compose -f docker-compose.prod.yml up -d --build

# Check service health
docker compose -f docker-compose.prod.yml ps
```


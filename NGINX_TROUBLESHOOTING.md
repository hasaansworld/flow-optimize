# Nginx Troubleshooting Guide

If nginx is not working, follow these steps:

## Quick Fix

```bash
# Run the automated fix script
./fix-nginx.sh

# Or manually restart
docker compose -f docker-compose.prod.yml restart nginx
```

## Check Nginx Logs

```bash
# View recent logs
docker logs wastewater-nginx

# Follow logs in real-time
docker logs -f wastewater-nginx
```

## Common Issues and Solutions

### 1. Nginx Configuration Error

**Symptoms:** Container keeps restarting, logs show "configuration file test failed"

**Fix:**
```bash
# Test nginx configuration
docker exec wastewater-nginx nginx -t

# If errors found, check nginx/nginx.conf for syntax errors
nano nginx/nginx.conf
```

### 2. Port 80 Already in Use

**Symptoms:** "failed to bind host port 0.0.0.0:80/tcp: address already in use"

**Fix:**
```bash
# Run port conflict fix
./fix-port-80.sh

# Or manually stop conflicting service
sudo systemctl stop apache2
sudo systemctl stop nginx
```

### 3. Health Check Failing

**Symptoms:** Container shows "health: starting" or "unhealthy"

**Fix:**
```bash
# Check if health endpoint works
docker exec wastewater-nginx wget -qO- http://localhost/health

# If wget not found, it will be installed automatically on next restart
docker compose -f docker-compose.prod.yml restart nginx
```

### 4. Upstream Services Not Available

**Symptoms:** 502 Bad Gateway errors

**Fix:**
```bash
# Check if backend services are running
docker compose -f docker-compose.prod.yml ps

# Ensure all services are up
docker compose -f docker-compose.prod.yml up -d

# Check nginx can reach services
docker exec wastewater-nginx ping -c 1 frontend
docker exec wastewater-nginx ping -c 1 agent-api
```

### 5. Frontend Not Loading

**Symptoms:** Frontend shows 502 or connection refused

**Fix:**
```bash
# Check frontend container
docker logs wastewater-frontend

# Restart frontend
docker compose -f docker-compose.prod.yml restart frontend

# Rebuild if needed
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

## Debug Commands

```bash
# Full diagnostic
./debug-nginx.sh

# Test nginx config
docker exec wastewater-nginx nginx -t

# Check nginx process
docker exec wastewater-nginx ps aux | grep nginx

# Test from inside container
docker exec wastewater-nginx wget -qO- http://localhost/health

# Check network connectivity
docker exec wastewater-nginx ping -c 1 frontend
docker exec wastewater-nginx ping -c 1 agent-api

# View nginx error log
docker exec wastewater-nginx cat /var/log/nginx/error.log
```

## Restart Nginx

```bash
# Restart nginx only
docker compose -f docker-compose.prod.yml restart nginx

# Recreate nginx container
docker compose -f docker-compose.prod.yml up -d --force-recreate nginx

# Full restart of all services
docker compose -f docker-compose.prod.yml restart
```

## Verify Nginx is Working

```bash
# Check container status
docker ps | grep nginx

# Test from host
curl http://localhost/health

# Test from browser
# http://YOUR_SERVER_IP/health
```

## Still Not Working?

1. Check all logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify all services are running: `docker compose -f docker-compose.prod.yml ps`
3. Check system resources: `df -h` and `free -h`
4. Review nginx configuration: `cat nginx/nginx.conf`


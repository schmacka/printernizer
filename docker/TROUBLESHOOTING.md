# Docker Troubleshooting Guide

## Common Issues and Solutions

### 1. "exec /app/entrypoint.sh: no such file or directory"

**Symptoms:**
- Container fails to start immediately after being created
- Error appears in logs: `exec /app/entrypoint.sh: no such file or directory`
- Container exits with status code 1

**Root Cause:**
The Docker image was built with an incorrect build context. The Dockerfile expects to be built from the repository root so it can access all required files:
- `src/` (application source code)
- `frontend/` (web interface)
- `database_schema.sql` (database schema)
- `docker/entrypoint.sh` (startup script)

**Solution:**

```bash
# Step 1: Clean up any existing containers and images
docker-compose down
docker rm -f printernizer 2>/dev/null || true
docker rmi printernizer:latest 2>/dev/null || true

# Step 2: Rebuild correctly (choose one method)

# Method A: Using docker-compose (recommended)
cd docker
docker-compose build --no-cache
docker-compose up -d

# Method B: Using build script
cd ..  # Go to repo root
./build-docker.sh

# Method C: Manual build
cd ..  # Go to repo root
docker build -f docker/Dockerfile -t printernizer:latest .
docker run -d -p 8000:8000 --name printernizer printernizer:latest
```

**Prevention:**
- Always use `docker-compose` from the `docker/` directory, OR
- Always use `./build-docker.sh` from the repository root, OR
- When building manually, ensure the build context is the repository root

**❌ WRONG (will cause the error):**
```bash
cd docker
docker build -t printernizer .  # Context is docker/, not repo root
```

**✅ CORRECT:**
```bash
cd docker
docker-compose up -d  # Compose handles the context correctly
```

---

### 2. Container Won't Start (General)

**Check logs first:**
```bash
docker-compose logs
docker logs printernizer
```

**Rebuild container:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

### 3. Database Issues

**Symptom:** Database connection errors or corruption

**Solution:**
```bash
# Backup existing data first (if any)
docker run --rm -v printernizer_printernizer-data:/data -v $(pwd):/backup alpine tar czf /backup/printernizer-backup.tar.gz /data

# Reset database (WARNING: deletes all data!)
docker-compose down
docker volume rm printernizer_printernizer-data
docker-compose up -d
```

---

### 4. Network Connectivity Issues

**Symptom:** Can't connect to printers

**Test connectivity:**
```bash
# Test from container
docker-compose exec printernizer ping 192.168.1.100

# Check container network
docker network inspect printernizer_printernizer-network
```

**Solution for printer discovery:**
If using printer auto-discovery (SSDP/mDNS), you may need host networking:

Edit `docker-compose.yml`:
```yaml
services:
  printernizer:
    network_mode: host  # Enable this
    # Comment out the 'networks' and 'ports' sections
```

---

### 5. Permission Issues

**Symptom:** Cannot write to database or files

**Solution:**
```bash
# Check container logs for permission errors
docker-compose logs | grep -i permission

# Fix volume permissions
docker-compose down
docker volume rm printernizer_printernizer-data
docker-compose up -d
```

---

### 6. Port Already in Use

**Symptom:** `Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use`

**Solution:**
```bash
# Find what's using port 8000
sudo lsof -i :8000
# or
sudo netstat -tulpn | grep :8000

# Either stop the conflicting service or change the port
# Edit docker-compose.yml:
ports:
  - "3000:8000"  # Use port 3000 instead
```

---

### 7. Out of Memory Errors

**Symptom:** Container killed or OOM errors in logs

**Solution:**
Increase memory limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 512M
```

---

### 8. Slow Performance

**Solutions:**

1. **Database vacuum:**
   ```bash
   docker-compose exec printernizer sqlite3 /app/data/printernizer.db "VACUUM;"
   ```

2. **Clear cache:**
   ```bash
   docker-compose exec printernizer rm -rf /app/data/preview-cache/*
   ```

3. **Check resource usage:**
   ```bash
   docker stats printernizer
   ```

---

## Health Checks

### Check if container is healthy:
```bash
# Method 1: Docker inspect
docker inspect printernizer | jq '.[0].State.Health'

# Method 2: Health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "..."
}
```

---

## Debugging

### Access container shell:
```bash
docker-compose exec printernizer bash
```

### Check file system:
```bash
# Verify entrypoint exists
docker-compose exec printernizer ls -la /app/entrypoint.sh

# Check application files
docker-compose exec printernizer ls -la /app/src/

# Check database
docker-compose exec printernizer ls -la /app/data/
```

### View live logs:
```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Application logs only
docker-compose exec printernizer tail -f /app/logs/app.log
```

---

## Still Having Issues?

1. **Check the main documentation:**
   - [docker/README.md](README.md)
   - [../README.md](../README.md)

2. **Enable debug logging:**
   Edit `docker-compose.yml`:
   ```yaml
   environment:
     - LOG_LEVEL=debug
   ```

3. **Verify prerequisites:**
   - Docker Engine 20.10+
   - Docker Compose 2.0+
   - Network access to printers
   - Sufficient disk space (at least 2GB)

4. **Report an issue:**
   https://github.com/schmacka/printernizer/issues

---

**Last Updated:** 2025-11-11

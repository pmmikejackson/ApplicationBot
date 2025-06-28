# ApplicationBot NAS Deployment Guide

## 🏠 Deploy ApplicationBot on Your NAS

### **Method 1: Docker Compose via Web UI**

#### **Step 1: Prepare Files**
1. Ensure all ApplicationBot files are accessible on your NAS
2. Edit `.env` file and update the frontend URL:
   ```env
   # Replace 'your-nas-ip' with your actual NAS IP address
   REACT_APP_API_URL=http://192.168.1.100:8000
   ```

#### **Step 2: Deploy via NAS Web Interface**

**Option A: If your NAS supports Docker Compose directly:**
1. Open your NAS Docker web interface
2. Navigate to "Compose" or "Stacks" section
3. Create new stack named "ApplicationBot"
4. Copy the contents of `docker-compose.yml`
5. Deploy the stack

**Option B: If deploying containers individually:**

1. **Create Network:**
   - Name: `applicationbot-network`
   - Type: Bridge

2. **Deploy PostgreSQL:**
   ```
   Image: postgres:15
   Container Name: applicationbot-postgres
   Ports: 5432:5432
   Environment Variables:
     POSTGRES_DB=applicationbot
     POSTGRES_USER=applicationbot
     POSTGRES_PASSWORD=applicationbot_secure_password_2024
   Volumes:
     postgres_data:/var/lib/postgresql/data
   Network: applicationbot-network
   ```

3. **Deploy Redis:**
   ```
   Image: redis:7-alpine
   Container Name: applicationbot-redis
   Ports: 6379:6379
   Network: applicationbot-network
   ```

4. **Build and Deploy Backend:**
   ```
   Build from: /path/to/ApplicationBot/backend/Dockerfile
   Container Name: applicationbot-backend
   Ports: 8000:8000
   Environment File: /path/to/ApplicationBot/.env
   Volumes:
     /path/to/ApplicationBot/backend:/app
     /path/to/ApplicationBot/documents:/app/documents
   Network: applicationbot-network
   Command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Build and Deploy Celery Worker:**
   ```
   Build from: /path/to/ApplicationBot/backend/Dockerfile
   Container Name: applicationbot-celery
   Environment File: /path/to/ApplicationBot/.env
   Volumes:
     /path/to/ApplicationBot/backend:/app
     /path/to/ApplicationBot/documents:/app/documents
   Network: applicationbot-network
   Command: celery -A app.core.celery worker --loglevel=info
   ```

6. **Build and Deploy Frontend:**
   ```
   Build from: /path/to/ApplicationBot/frontend/Dockerfile
   Container Name: applicationbot-frontend
   Ports: 3000:3000
   Environment Variables:
     REACT_APP_API_URL=http://YOUR_NAS_IP:8000
   Volumes:
     /path/to/ApplicationBot/frontend:/app
   Network: applicationbot-network
   Command: npm start
   ```

### **Step 3: Initialize Database**
1. Access the backend container terminal through your NAS web interface
2. Run database migrations:
   ```bash
   alembic upgrade head
   ```
3. Create default document templates:
   ```bash
   python -c "from app.services.document_service import DocumentCustomizationService; DocumentCustomizationService().create_default_templates()"
   ```

### **Step 4: Access ApplicationBot**
- **Dashboard:** http://YOUR_NAS_IP:3000
- **API Docs:** http://YOUR_NAS_IP:8000/docs
- **Backend Health:** http://YOUR_NAS_IP:8000/health

### **Method 2: Manual Docker Commands (SSH)**

If you have SSH access to your NAS, you can also deploy using command line:

```bash
# Navigate to ApplicationBot directory
cd /path/to/ApplicationBot

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Initialize database
docker-compose exec backend alembic upgrade head
```

### **Port Configuration**

Make sure these ports are available on your NAS:
- **3000**: Frontend dashboard
- **8000**: Backend API
- **5432**: PostgreSQL (internal)
- **6379**: Redis (internal)

### **Firewall Settings**

If you want to access ApplicationBot from other devices on your network:
1. Open ports 3000 and 8000 in your NAS firewall
2. Or set up port forwarding if accessing from outside your network

### **First-Time Setup**

Once deployed:

1. **Access the dashboard:** http://YOUR_NAS_IP:3000
2. **Configure your profile:**
   - Go to Settings
   - Add your personal information
   - Set job preferences and target titles
   - Upload resume template
3. **Add platform credentials (optional):**
   - LinkedIn and Indeed credentials for automated applications
4. **Start job discovery:**
   - Click "Start Job Search" in the dashboard
   - Monitor the Jobs tab for discovered opportunities

### **Maintenance**

- **View logs:** Use your NAS Docker interface to monitor container logs
- **Update:** Pull latest code and rebuild containers
- **Backup:** Regular database backups via PostgreSQL container
- **Monitor:** Check container resource usage and restart if needed

### **Troubleshooting**

**Common Issues:**
1. **Build failures:** Ensure sufficient disk space and memory
2. **Database connection:** Verify PostgreSQL container is running
3. **Frontend can't reach API:** Check REACT_APP_API_URL matches your NAS IP
4. **Permission errors:** Ensure proper file permissions on mounted volumes

**Container Resource Requirements:**
- **Total RAM:** ~2-4GB recommended
- **Storage:** ~5-10GB for containers + job data
- **CPU:** 2+ cores recommended for background tasks

### **Security Considerations**

- Change default passwords in `.env`
- Use strong SECRET_KEY (already generated)
- Consider VPN access if exposing to internet
- Regular security updates for container images
- Monitor access logs for unusual activity
# Deployment Guide

## Quick Start Deployment

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Local Development Setup

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd blockchain-cloud-scheduler
   
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the System**
   ```bash
   # Start the API server
   python backend.py
   
   # In another terminal or open simulation.html in browser
   open simulation.html
   ```

4. **Access the Application**
   - API Server: `http://localhost:8000`
   - Web Interface: Open `simulation.html` in your browser
   - API Documentation: `http://localhost:8000/docs`

## Production Deployment

### Docker Deployment

1. **Build Docker Image**
   ```bash
   # Create Dockerfile
   cat > Dockerfile << EOF
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   EXPOSE 8000
   
   CMD ["python", "backend.py"]
   EOF
   
   # Build image
   docker build -t blockchain-scheduler:latest .
   ```

2. **Run with Docker Compose**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   
   services:
     scheduler-api:
       build: .
       ports:
         - "8000:8000"
       environment:
         - PYTHONPATH=/app
         - LEDGER_BLOCK_SIZE=10
       volumes:
         - ./data:/app/data
       restart: unless-stopped
   
     scheduler-ui:
       image: nginx:alpine
       ports:
         - "80:80"
       volumes:
         - ./simulation.html:/usr/share/nginx/html/index.html
         - ./nginx.conf:/etc/nginx/nginx.conf
       depends_on:
         - scheduler-api
       restart: unless-stopped
   
   volumes:
     data:
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Kubernetes Deployment

1. **Create Kubernetes Manifests**
   ```yaml
   # k8s-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: blockchain-scheduler
     labels:
       app: blockchain-scheduler
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: blockchain-scheduler
     template:
       metadata:
         labels:
           app: blockchain-scheduler
       spec:
         containers:
         - name: scheduler
           image: blockchain-scheduler:latest
           ports:
           - containerPort: 8000
           env:
           - name: LEDGER_PERSISTENCE
             value: "memory"
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
           livenessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 5
             periodSeconds: 5
   
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: scheduler-service
   spec:
     selector:
       app: blockchain-scheduler
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8000
     type: LoadBalancer
   
   ---
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: scheduler-ingress
     annotations:
       kubernetes.io/ingress.class: nginx
       cert-manager.io/cluster-issuer: letsencrypt-prod
   spec:
     tls:
     - hosts:
       - scheduler.yourdomain.com
       secretName: scheduler-tls
     rules:
     - host: scheduler.yourdomain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: scheduler-service
               port:
                 number: 80
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s-deployment.yaml
   kubectl get pods -l app=blockchain-scheduler
   kubectl get services
   ```

### Cloud Platform Deployment

#### AWS Deployment

1. **Using AWS ECS**
   ```json
   {
     "family": "blockchain-scheduler",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "scheduler",
         "image": "your-account.dkr.ecr.region.amazonaws.com/blockchain-scheduler:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/blockchain-scheduler",
             "awslogs-region": "us-west-2",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

2. **Deploy with AWS CLI**
   ```bash
   # Register task definition
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   
   # Create service
   aws ecs create-service \
     --cluster your-cluster \
     --service-name blockchain-scheduler \
     --task-definition blockchain-scheduler:1 \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Azure Deployment

1. **Using Azure Container Instances**
   ```bash
   # Create resource group
   az group create --name blockchain-scheduler-rg --location eastus
   
   # Deploy container
   az container create \
     --resource-group blockchain-scheduler-rg \
     --name blockchain-scheduler \
     --image blockchain-scheduler:latest \
     --dns-name-label blockchain-scheduler-unique \
     --ports 8000 \
     --cpu 1 \
     --memory 1
   ```

#### Google Cloud Platform

1. **Using Cloud Run**
   ```bash
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/PROJECT-ID/blockchain-scheduler
   
   # Deploy to Cloud Run
   gcloud run deploy blockchain-scheduler \
     --image gcr.io/PROJECT-ID/blockchain-scheduler \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8000 \
     --memory 512Mi \
     --cpu 1
   ```

## Configuration Management

### Environment Variables

```bash
# Core Configuration
LEDGER_BLOCK_SIZE=10                    # Transactions per block
SCHEDULER_ALGORITHM=blockchain          # Default scheduler
VM_CAPACITY_CPU=500                     # Default VM CPU capacity
VM_CAPACITY_MEM=250                     # Default VM memory capacity
VM_CAPACITY_IO=300                      # Default VM I/O capacity
VM_CAPACITY_BW=20                       # Default VM bandwidth capacity

# Performance Tuning
MAX_CONCURRENT_REQUESTS=100             # API rate limiting
CACHE_TTL=300                          # Cache timeout in seconds
LEDGER_VALIDATION_INTERVAL=60          # Chain validation frequency

# Security
API_KEY_REQUIRED=false                 # Enable API key authentication
CORS_ORIGINS=*                         # Allowed CORS origins
RATE_LIMIT_PER_MINUTE=1000            # API rate limiting

# Monitoring
METRICS_ENABLED=true                   # Enable metrics collection
LOG_LEVEL=INFO                         # Logging level
HEALTH_CHECK_INTERVAL=30               # Health check frequency
```

### Configuration Files

1. **Create config.yaml**
   ```yaml
   # config.yaml
   server:
     host: "0.0.0.0"
     port: 8000
     workers: 4
   
   ledger:
     block_size: 10
     validation_enabled: true
     persistence: "memory"  # Options: memory, sqlite, postgresql
   
   schedulers:
     default: "blockchain"
     blockchain:
       alpha: 0.7
       beta: 0.3
       history_window: 10
     
   vm_defaults:
     cpu: 500
     memory: 250
     io: 300
     bandwidth: 20
   
   monitoring:
     metrics_enabled: true
     health_checks: true
     log_level: "INFO"
   ```

2. **Load Configuration in Application**
   ```python
   # config.py
   import yaml
   import os
   
   def load_config():
       config_path = os.getenv('CONFIG_PATH', 'config.yaml')
       with open(config_path, 'r') as f:
           return yaml.safe_load(f)
   
   CONFIG = load_config()
   ```

## Monitoring and Logging

### Application Monitoring

1. **Health Check Endpoint**
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "timestamp": datetime.utcnow().isoformat(),
           "version": "1.0.0",
           "ledger_integrity": validate_ledger_integrity(),
           "active_schedulers": len(SCHEDULERS)
       }
   ```

2. **Metrics Collection**
   ```python
   # Add to requirements.txt
   prometheus-client==0.14.1
   
   # metrics.py
   from prometheus_client import Counter, Histogram, Gauge, generate_latest
   
   # Define metrics
   REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
   REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
   ACTIVE_VMS = Gauge('active_vms_total', 'Number of active VMs')
   LEDGER_SIZE = Gauge('ledger_blocks_total', 'Total blocks in ledger')
   
   @app.get("/metrics")
   async def metrics():
       return Response(generate_latest(), media_type="text/plain")
   ```

### Logging Configuration

```python
# logging_config.py
import logging
import sys
from datetime import datetime

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('scheduler.log')
        ]
    )
    
    # Create logger for scheduler events
    scheduler_logger = logging.getLogger('scheduler')
    scheduler_logger.setLevel(logging.INFO)
    
    return scheduler_logger
```

## Security Configuration

### SSL/TLS Setup

1. **Generate SSL Certificates**
   ```bash
   # Self-signed certificate for development
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   
   # For production, use Let's Encrypt
   certbot certonly --standalone -d yourdomain.com
   ```

2. **Configure HTTPS**
   ```python
   # backend.py
   import ssl
   
   if __name__ == "__main__":
       ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
       ssl_context.load_cert_chain('cert.pem', 'key.pem')
       
       uvicorn.run(
           app, 
           host="0.0.0.0", 
           port=8000,
           ssl_keyfile="key.pem",
           ssl_certfile="cert.pem"
       )
   ```

### API Security

```python
# security.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

# Apply to protected endpoints
@app.post("/schedule")
async def schedule_task(request: ScheduleRequest, token: str = Depends(verify_token)):
    # Protected endpoint logic
    pass
```

## Performance Optimization

### Database Optimization

```python
# For persistent storage
DATABASE_URL = "postgresql://user:password@localhost/scheduler_db"

# Connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### Caching Configuration

```python
# Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Module Import Errors**
   ```bash
   # Ensure virtual environment is activated
   which python
   pip list
   ```

3. **CORS Issues**
   ```python
   # Add to backend.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Debug Mode

```python
# Enable debug mode
if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        debug=True,
        reload=True
    )
```

### Log Analysis

```bash
# Monitor logs in real-time
tail -f scheduler.log

# Search for errors
grep "ERROR" scheduler.log

# Analyze performance
grep "scheduling_latency" scheduler.log | awk '{print $NF}' | sort -n
```

This deployment guide provides comprehensive instructions for deploying the blockchain-integrated cloud scheduler in various environments, from local development to production cloud platforms.
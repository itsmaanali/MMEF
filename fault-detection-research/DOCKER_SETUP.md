# Docker Setup Guide - Fault Detection Research

## Quick Start (TL;DR)

```bash
# 1. Clone the repository
git clone <repository-url>
cd fault-detection-research

# 2. Build and run
docker-compose up -d

# 3. Enter the environment
docker exec -it fault-detection-env bash

# 4. Run experiments
python3 train_models_demo.py
```

---

## 📋 Prerequisites

### Required Software

1. **Docker Desktop** (or Docker Engine + Docker Compose)
   - **macOS/Windows:** [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - **Linux:** Install via package manager
     ```bash
     # Ubuntu/Debian
     sudo apt-get update
     sudo apt-get install docker.io docker-compose

     # CentOS/RHEL
     sudo yum install docker docker-compose
     ```

2. **Git** (for cloning repository)
   ```bash
   # Check if installed
   git --version
   ```

3. **Minimum System Requirements:**
   - **CPU:** 4 cores recommended (2 cores minimum)
   - **RAM:** 8 GB recommended (4 GB minimum)
   - **Disk:** 10 GB free space
   - **OS:** Linux, macOS, or Windows 10/11 with WSL2

---

## 🚀 Installation Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd fault-detection-research

# Verify files
ls -la
# Should see: Dockerfile, docker-compose.yml, requirements.txt, etc.
```

### Step 2: Build Docker Image

```bash
# Build the Docker image (first time only, takes 5-10 minutes)
docker-compose build

# Or build manually
docker build -t fault-detection-research:latest .
```

**Build Output:**
```
[+] Building 245.3s (15/15) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [1/9] FROM docker.io/library/python:3.13-slim
 => [2/9] RUN apt-get update && apt-get install -y ...
 => [3/9] RUN pip install --upgrade pip setuptools wheel
 => [4/9] COPY requirements.txt /workspace/
 => [5/9] RUN pip install --no-cache-dir -r requirements.txt
 => [6/9] COPY . /workspace/
 => exporting to image
```

### Step 3: Start Container

```bash
# Start the container in background
docker-compose up -d

# Check running containers
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                              STATUS         PORTS
abc123def456   fault-detection-research:latest   Up 10 seconds  8888->8888/tcp
```

### Step 4: Enter Container

```bash
# Interactive bash shell
docker exec -it fault-detection-env bash

# You should see:
root@abc123def456:/workspace#
```

---

## 🔧 Usage

### Running Experiments Inside Container

```bash
# Once inside container:
root@abc123def456:/workspace#

# Run demo training
python3 train_models_demo.py

# Run multi-modal detection
python3 train_multimodal_detection.py

# Run enhanced training with SMOTE
python3 train_real_datasets_enhanced.py

# Generate sample data
python3 generate_sample_data.py

# Check Python environment
python3 -c "import numpy, pandas, sklearn; print('All dependencies OK!')"
```

### Accessing Files

**From Host Machine:**
```bash
# Files in container are synced with host
ls models/        # See trained models
ls output/plots/  # See generated visualizations
```

**From Container:**
```bash
# Inside container
ls /workspace/models/
ls /workspace/output/plots/
```

### Copying Files In/Out

```bash
# Copy file INTO container
docker cp mydata.csv fault-detection-env:/workspace/datasets/

# Copy file OUT of container
docker cp fault-detection-env:/workspace/models/my_model.pkl ./

# Copy entire directory
docker cp fault-detection-env:/workspace/output/ ./results/
```

---

## 📊 Running Specific Experiments

### Experiment #001: Synthetic Demo

```bash
docker exec -it fault-detection-env bash
python3 train_models_demo.py
```

### Experiment #003: Multi-Modal Fusion

```bash
docker exec -it fault-detection-env bash

# Generate data
python3 generate_multimodal_dataset.py

# Train models
python3 train_multimodal_detection.py
```

### Experiment #005: Enhanced with SMOTE

```bash
docker exec -it fault-detection-env bash

# Requires real datasets (provide via volume mount or copy)
# See "Mounting External Data" section below

python3 train_real_datasets_enhanced.py
```

---

## 💾 Data Management

### Mounting External Datasets

**Option 1: Via docker-compose.yml (Recommended)**

Edit `docker-compose.yml`:
```yaml
volumes:
  - .:/workspace
  - ${HOME}/Downloads:/downloads:ro  # Mount Downloads folder
  - /path/to/your/datasets:/workspace/datasets/external:ro
```

**Option 2: Manual Mount**

```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/Downloads:/downloads:ro \
  fault-detection-research:latest \
  bash
```

### Persistent Storage

Docker volumes are used for persistence:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect fault-detection-research_models-data

# Backup volume
docker run --rm -v fault-detection-research_models-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/models-backup.tar.gz /data

# Restore volume
docker run --rm -v fault-detection-research_models-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/models-backup.tar.gz -C /
```

---

## 🌐 Optional: Jupyter Notebook

### Start Jupyter Lab

```bash
# Start with Jupyter profile
docker-compose --profile jupyter up -d

# Access Jupyter at: http://localhost:8888
# No password required (configured for local development)
```

### Manual Jupyter Start

```bash
# Inside container
pip install jupyter jupyterlab
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

---

## 🛠️ Advanced Usage

### Custom Resource Limits

Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'      # Use 8 CPU cores
      memory: 16G      # Use 16 GB RAM
```

### Running Multiple Experiments in Parallel

```bash
# Terminal 1
docker exec -it fault-detection-env bash
python3 train_models_demo.py

# Terminal 2 (new window)
docker exec -it fault-detection-env bash
python3 generate_multimodal_dataset.py

# Both run simultaneously in same container
```

### Installing Additional Packages

```bash
# Temporary (lost on container restart)
docker exec -it fault-detection-env bash
pip install xgboost lightgbm

# Permanent (modify Dockerfile)
# Add to requirements.txt:
xgboost>=2.0.0
lightgbm>=4.3.0

# Rebuild image
docker-compose build
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs fault-detection

# Check if port is already in use
lsof -i :8888  # macOS/Linux
netstat -ano | findstr :8888  # Windows

# Remove old containers
docker-compose down
docker-compose up -d
```

### "Permission Denied" Errors

```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up -d
```

### Out of Memory

```bash
# Check Docker resources
docker stats

# Increase Docker Desktop memory limit
# Docker Desktop → Preferences → Resources → Memory → 8 GB
```

### Python Package Issues

```bash
# Rebuild with no cache
docker-compose build --no-cache

# Check Python version
docker exec -it fault-detection-env python3 --version
# Should be: Python 3.13.x
```

### Files Not Syncing

```bash
# Check volume mounts
docker inspect fault-detection-env | grep Mounts -A 10

# Restart container
docker-compose restart

# Force recreate
docker-compose up -d --force-recreate
```

---

## 🧹 Cleanup

### Stop Container

```bash
# Stop container (preserves volumes)
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Remove Image

```bash
# Remove image
docker rmi fault-detection-research:latest

# Remove all unused images
docker image prune -a
```

### Complete Cleanup

```bash
# Remove everything (containers, volumes, images)
docker-compose down -v --rmi all

# Remove all Docker data (CAUTION: affects all Docker projects)
docker system prune -a --volumes
```

---

## 📁 Project Structure Inside Container

```
/workspace/
├── datasets/                      # Datasets
│   ├── hdfs_faults_sample.csv
│   ├── multimodal/
│   └── processed/
├── models/                        # Trained models (persistent)
│   ├── random_forest.pkl
│   ├── multimodal/
│   └── real_datasets_enhanced/
├── output/                        # Results (persistent)
│   ├── plots/
│   └── telemetry/
├── python/                        # Python source code
│   ├── models/
│   └── training/
├── src/                           # Java source (CloudSim)
├── train_*.py                     # Training scripts
├── generate_*.py                  # Data generation scripts
├── requirements.txt               # Python dependencies
├── EXPERIMENT_LOG.md             # Experiment results
└── README.md                      # Documentation
```

---

## 🚀 Quick Commands Reference

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Enter container
docker exec -it fault-detection-env bash

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Check status
docker ps

# Run single command
docker exec fault-detection-env python3 train_models_demo.py

# Copy files
docker cp fault-detection-env:/workspace/models/model.pkl ./

# Start Jupyter
docker-compose --profile jupyter up -d
```

---

## 🌟 Best Practices

### 1. Use Volume Mounts for Large Datasets

```yaml
# docker-compose.yml
volumes:
  - ~/datasets:/workspace/datasets/external:ro
```

### 2. Save Models Regularly

```bash
# Backup models from container
docker cp fault-detection-env:/workspace/models/ ./backup-$(date +%Y%m%d)/
```

### 3. Use .dockerignore

Already configured to exclude:
- Large datasets (.csv.gz, .tar.gz)
- Python cache (\__pycache\__)
- Git files
- IDE files

### 4. Monitor Resources

```bash
# Real-time stats
docker stats fault-detection-env

# View container resource usage
docker exec fault-detection-env top
```

### 5. Keep Images Updated

```bash
# Pull latest base image
docker pull python:3.13-slim

# Rebuild
docker-compose build --no-cache
```

---

## 📚 Additional Resources

- **Docker Documentation:** https://docs.docker.com/
- **Docker Compose Reference:** https://docs.docker.com/compose/
- **Python Docker Best Practices:** https://docs.docker.com/language/python/
- **Project README:** [README.md](README.md)
- **Experiment Log:** [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md)

---

## 💡 Tips

### Tip 1: Use Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias fd-enter='docker exec -it fault-detection-env bash'
alias fd-start='docker-compose up -d'
alias fd-stop='docker-compose down'
alias fd-logs='docker-compose logs -f'
```

### Tip 2: Auto-Restart on Failure

Edit `docker-compose.yml`:
```yaml
restart: unless-stopped
```

### Tip 3: Run as Non-Root (Security)

Modify Dockerfile:
```dockerfile
# Add user
RUN useradd -m -u 1000 researcher
USER researcher
```

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
# 1. Container running
docker ps | grep fault-detection
# ✅ Should show running container

# 2. Python environment
docker exec fault-detection-env python3 --version
# ✅ Python 3.13.x

# 3. Dependencies installed
docker exec fault-detection-env python3 -c "import numpy, pandas, sklearn, imblearn; print('OK')"
# ✅ OK

# 4. Java installed (for CloudSim)
docker exec fault-detection-env java -version
# ✅ openjdk version "17.x.x"

# 5. Files accessible
docker exec fault-detection-env ls -la /workspace
# ✅ Should see project files

# 6. Run test
docker exec fault-detection-env python3 -c "from sklearn.ensemble import RandomForestClassifier; print('Scikit-learn OK')"
# ✅ Scikit-learn OK
```

---

## 🎓 Summary

**What You Get:**
- ✅ Exact Python 3.13 environment
- ✅ All ML dependencies pre-installed
- ✅ Persistent storage for models and results
- ✅ Java 17 for CloudSim
- ✅ Optional Jupyter Lab
- ✅ Reproducible environment across any machine

**What You Don't Need:**
- ❌ Manual Python installation
- ❌ Dependency management
- ❌ Environment configuration
- ❌ Compatibility issues

**One Command Setup:**
```bash
docker-compose up -d && docker exec -it fault-detection-env bash
```

**You're Ready!** 🎉

---

**Last Updated:** October 15, 2025
**Docker Image:** fault-detection-research:latest
**Base Image:** python:3.13-slim
**Maintained By:** Fault Detection Research Team

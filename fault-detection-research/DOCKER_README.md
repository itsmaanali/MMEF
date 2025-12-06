# 🐳 Docker Setup - Quick Reference

## One-Line Setup

```bash
./docker-quickstart.sh
```

**That's it!** The script will:
1. ✅ Check prerequisites (Docker, Docker Compose)
2. ✅ Build the Docker image (~5-10 min first time)
3. ✅ Start the container
4. ✅ Run verification tests
5. ✅ Enter the container automatically

---

## Manual Setup (3 Commands)

```bash
# 1. Build
docker-compose build

# 2. Start
docker-compose up -d

# 3. Enter
docker exec -it fault-detection-env bash
```

---

## What's Included

### Environment
- **Python:** 3.13 (latest)
- **OS:** Debian-based Linux (slim)
- **Java:** OpenJDK 17 (for CloudSim)

### Pre-installed Libraries
- **Scientific:** numpy, scipy, pandas
- **ML:** scikit-learn, imbalanced-learn (SMOTE)
- **Visualization:** matplotlib, seaborn
- **Utilities:** joblib, tqdm, pyyaml

### Project Files
- ✅ All Python scripts
- ✅ Training pipelines
- ✅ Dataset generators
- ✅ Documentation
- ✅ Experiment logs

---

## Common Commands

| Task | Command |
|------|---------|
| **Enter container** | `docker exec -it fault-detection-env bash` |
| **Run experiment** | `docker exec fault-detection-env python3 train_models_demo.py` |
| **View logs** | `docker-compose logs -f` |
| **Stop container** | `docker-compose down` |
| **Restart** | `docker-compose restart` |
| **Rebuild** | `docker-compose build --no-cache` |
| **Copy files out** | `docker cp fault-detection-env:/workspace/models/ ./` |
| **Check status** | `docker ps` |

---

## Running Experiments

### Inside Container
```bash
# Enter container
docker exec -it fault-detection-env bash

# Run experiments
python3 train_models_demo.py                    # Experiment #001
python3 train_hdfs_anomaly_detection.py         # Experiment #002
python3 train_multimodal_detection.py           # Experiment #003
python3 train_real_datasets_enhanced.py         # Experiment #005
```

### From Host (without entering)
```bash
docker exec fault-detection-env python3 train_models_demo.py
docker exec fault-detection-env python3 generate_sample_data.py
```

---

## Data Persistence

### Volumes (Automatically Persisted)
- `models/` - Trained models saved here
- `output/` - Plots and results saved here
- `datasets/` - Processed datasets saved here

### Accessing from Host
Files are automatically synced:
```bash
ls models/          # View models on host
ls output/plots/    # View plots on host
```

---

## Mounting External Data

### Option 1: Edit docker-compose.yml
```yaml
volumes:
  - .:/workspace
  - ~/Downloads:/downloads:ro
  - /path/to/datasets:/workspace/datasets/external:ro
```

### Option 2: Copy Into Container
```bash
docker cp mydata.csv fault-detection-env:/workspace/datasets/
```

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs fault-detection
docker-compose down && docker-compose up -d
```

### Permission errors
```bash
# Linux only
sudo usermod -aG docker $USER
newgrp docker
```

### Out of memory
```bash
# Docker Desktop: Settings → Resources → Memory → 8 GB
docker stats  # Check current usage
```

### Python package missing
```bash
docker exec fault-detection-env pip install <package-name>

# Or add to requirements.txt and rebuild:
docker-compose build --no-cache
```

---

## Advanced Features

### Jupyter Notebook (Optional)
```bash
docker-compose --profile jupyter up -d
# Access at: http://localhost:8888
```

### Resource Limits
Edit `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 16G
```

### Run as Non-Root
Edit `Dockerfile`:
```dockerfile
RUN useradd -m researcher
USER researcher
```

---

## File Structure

```
/workspace/
├── datasets/          # Data
├── models/            # Trained models (persistent)
├── output/            # Results (persistent)
│   ├── plots/
│   └── telemetry/
├── train_*.py         # Training scripts
├── generate_*.py      # Data generators
└── *.md              # Documentation
```

---

## Cleanup

```bash
# Stop container
docker-compose down

# Remove volumes too
docker-compose down -v

# Remove image
docker rmi fault-detection-research:latest

# Complete cleanup
docker system prune -a --volumes
```

---

## Full Documentation

📖 **Comprehensive Guide:** [DOCKER_SETUP.md](DOCKER_SETUP.md)
- Prerequisites
- Step-by-step installation
- Advanced usage
- Troubleshooting
- Best practices

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disk** | 5 GB free | 10+ GB free |
| **OS** | Any with Docker | Linux/macOS/Windows 10+ |

---

## Quick Verification

```bash
# Check everything works
docker exec fault-detection-env python3 -c "
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
print('✓ All dependencies OK!')
"
```

---

## Support

**Issues?**
1. Check [DOCKER_SETUP.md](DOCKER_SETUP.md) (comprehensive guide)
2. View logs: `docker-compose logs -f`
3. Restart: `docker-compose restart`
4. Rebuild: `docker-compose build --no-cache`

**Still stuck?**
- Docker docs: https://docs.docker.com/
- Project README: [README.md](README.md)

---

**Last Updated:** October 15, 2025
**Docker Image:** fault-detection-research:latest
**Base:** python:3.13-slim

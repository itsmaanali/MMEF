# Dataset Guide

This document provides instructions for obtaining and preparing the datasets used in this research project.

## Overview

The fault detection system uses the following open-source datasets:

1. **Google Cluster Trace** - Workload and resource usage data
2. **Alibaba Cluster Trace** - Container resource usage and failures
3. **BGL System Logs** - Blue Gene/L supercomputer system logs
4. **NASA Prognostics Datasets** - Battery and turbofan engine degradation data

## Dataset Descriptions

### 1. Google Cluster Trace

**Source**: https://github.com/google/cluster-data

**Description**: Resource usage traces from a Google compute cluster containing workload characteristics, machine events, and resource consumption.

**Files Needed**:
- `machine_events/*.csv` - Machine lifecycle events
- `task_usage/*.csv` - CPU and memory usage per task

**Download Instructions**:
```bash
mkdir -p datasets/google-cluster
cd datasets/google-cluster
# Download from Google Cloud Storage
gsutil -m cp -r gs://clusterdata-2011-2/* .
```

**Preprocessing**:
- Extract machine failure events
- Aggregate resource usage metrics
- Align timestamps

### 2. Alibaba Cluster Trace

**Source**: https://github.com/alibaba/clusterdata

**Description**: Production cluster traces from Alibaba datacenters, including container lifecycle, resource allocation, and failure information.

**Files Needed**:
- `machine_meta.csv` - Machine specifications
- `machine_usage.csv` - CPU, memory usage over time
- `container_meta.csv` - Container information
- `container_usage.csv` - Container resource usage

**Download Instructions**:
```bash
mkdir -p datasets/alibaba-cluster
cd datasets/alibaba-cluster
wget http://alibaba-clusterdata.oss-cn-hangzhou.aliyuncs.com/cluster-trace-v2018/machine_meta.tar.gz
wget http://alibaba-clusterdata.oss-cn-hangzhou.aliyuncs.com/cluster-trace-v2018/machine_usage.tar.gz
tar -xzf machine_meta.tar.gz
tar -xzf machine_usage.tar.gz
```

### 3. BGL System Logs

**Source**: https://www.usenix.org/cfdr-data

**Description**: System logs from Blue Gene/L supercomputer at Lawrence Livermore National Laboratory. Contains error messages and failure indicators.

**Files Needed**:
- `BGL.log` - Raw system log file

**Download Instructions**:
```bash
mkdir -p datasets/bgl-logs
cd datasets/bgl-logs
wget https://zenodo.org/record/3227177/files/BGL.tar.gz
tar -xzf BGL.tar.gz
```

**Preprocessing**:
- Parse log messages
- Extract error categories
- Create time-series labels

### 4. NASA Prognostics Data

**Source**: https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/

**Description**: Battery and turbofan engine degradation datasets useful for understanding failure progression patterns.

**Files Needed**:
- Battery datasets: `B0005.mat`, `B0006.mat`, etc.
- Turbofan dataset: `train_FD001.txt`

**Download Instructions**:
```bash
mkdir -p datasets/nasa-prognostics
cd datasets/nasa-prognostics

# Battery data
wget https://ti.arc.nasa.gov/c/6/
# Extract battery mat files

# Turbofan engine data
wget https://ti.arc.nasa.gov/c/13/
unzip CMAPSSData.zip
```

## Data Preprocessing

After downloading datasets, run the preprocessing scripts:

```bash
cd python/preprocessing
python preprocess_all_datasets.py
```

This will:
1. Parse raw dataset formats
2. Extract relevant features
3. Normalize timestamps
4. Create unified CSV format
5. Generate ground truth labels

## Processed Data Format

All datasets are converted to a common CSV format:

```csv
timestamp,cpu_util,memory_util,power_w,temp_c,fault_label,fault_type
1234567890,0.65,0.72,250.5,45.2,0,NONE
1234567891,0.68,0.74,255.3,46.8,0,NONE
1234567892,0.95,0.88,380.2,78.5,1,THERMAL_ISSUE
```

## Dataset Statistics

| Dataset | Size | Duration | Fault Events | Fault Types |
|---------|------|----------|--------------|-------------|
| Google Cluster | ~40 GB | 29 days | ~12,000 | Machine failures, task evictions |
| Alibaba Cluster | ~200 GB | 8 days | ~15,000 | Container OOM, CPU throttling |
| BGL Logs | ~700 MB | 7 months | ~350,000 | Hardware errors, software failures |
| NASA Prognostics | ~50 MB | Various | ~200 | Battery degradation, turbine wear |

## Citation

If you use these datasets in your research, please cite the original sources:

```bibtex
@inproceedings{reiss2011google,
  title={Google cluster-usage traces: format+ schema},
  author={Reiss, Charles and Wilkes, John and Hellerstein, Joseph L},
  booktitle={Google Inc., White Paper},
  year={2011}
}

@inproceedings{alibaba2018,
  title={Alibaba cluster trace program},
  author={Alibaba},
  year={2018}
}

@inproceedings{oliner2007supercomputers,
  title={Supercomputers as a graveyard for dead computers},
  author={Oliner, Adam and Sahoo, Ramendra K and Moreira, Jose E and Gupta, Manish},
  booktitle={HotDep},
  year={2007}
}

@article{saha2009battery,
  title={Battery data set},
  author={Saha, Bhaskar and Goebel, Kai},
  journal={NASA AMES Prognostics Data Repository},
  year={2009}
}
```

## Troubleshooting

### Dataset Not Found
- Verify download URLs are still valid
- Check internet connection
- Ensure sufficient disk space (>300 GB recommended)

### Preprocessing Errors
- Ensure all required Python packages are installed
- Check file permissions
- Verify CSV encoding (should be UTF-8)

### Memory Issues
- Process datasets in chunks
- Use the `--batch-size` parameter
- Close other applications

For additional help, please open an issue in the repository.

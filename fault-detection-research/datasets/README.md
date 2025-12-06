# Official Dataset Integration Guide

This directory contains scripts to download, parse, and integrate official cluster traces into the fault detection research pipeline.

## Supported Datasets

### 1. Google Cluster Trace 2011 (v2)
- **Source**: https://github.com/google/cluster-data
- **Coverage**: 29 days of production cluster data
- **Size**: ~40GB compressed
- **Files Used**:
  - `machine_events/*.csv.gz` - Machine lifecycle events
  - `task_events/*.csv.gz` - Task submission, scheduling, failures
  - `task_usage/*.csv.gz` - Resource utilization over time

### 2. Google Cluster Trace 2019 (v3)
- **Source**: https://github.com/google/cluster-data/blob/master/ClusterData2019.md
- **Coverage**: 8 cells from May 2019
- **Includes**: PowerData2019 for power-aware simulation
- **Format**: Protobuf + CSV export tools

### 3. Alibaba Cluster Trace 2018
- **Source**: https://github.com/alibaba/clusterdata
- **Coverage**: ~4,000 machines, 8 days
- **Size**: ~200GB
- **Files Used**:
  - `machine_usage.csv` - CPU, memory, disk, network utilization
  - `batch_instance.csv` - Job/task lifecycle
  - `container_event.csv` - Container events
  - `machine_meta.csv` - Machine specifications

## Quick Start

### 1. Download Datasets

```bash
# Google Cluster Trace 2011
cd datasets
python download_google_2011.py --sample  # Downloads 1 day sample
# OR for full dataset:
# python download_google_2011.py --full

# Alibaba Cluster Trace 2018
python download_alibaba_2018.py --sample
```

### 2. Parse and Transform

```bash
# Parse Google traces to CloudSim format
python parse_google_2011.py \
  --input datasets/google-2011 \
  --output processed/google-2011

# Parse Alibaba traces
python parse_alibaba_2018.py \
  --input datasets/alibaba-2018 \
  --output processed/alibaba-2018
```

### 3. Generate ML Features

```bash
# Create fault-labeled feature store
python generate_features.py \
  --dataset google-2011 \
  --lead-time 3600  # 60-minute early warning
```

## Data Schemas

### Google 2011 Raw Format

```sql
-- machine_events.csv
timestamp, machine_id, event_type, platform_id, cpu_capacity, memory_capacity

-- task_events.csv
timestamp, job_id, task_index, machine_id, event_type, priority,
cpu_request, memory_request, disk_request

-- task_usage.csv
start_time, end_time, job_id, task_index, machine_id,
cpu_rate, canonical_memory_usage, assigned_memory,
disk_io_time, local_disk_space_usage, max_cpu_rate,
cycles_per_instruction, memory_accesses_per_instruction
```

### Alibaba 2018 Raw Format

```sql
-- machine_usage.csv
timestamp, machine_id, cpu_util_percent, mem_util_percent,
net_in, net_out, disk_io_percent

-- batch_instance.csv
job_id, task_id, instance_id, submit_time, start_time, end_time,
cpu_request, memory_request, cpu_used, memory_used, status
```

## CloudSim Mapping

### Hosts (from machines)
- `Host.id` ← `machine_id`
- `Host.pesNumber` ← `round(cpu_capacity)` (Google) or fixed (Alibaba)
- `Host.mipsPerPe` ← 10,000 MIPS baseline
- `Host.ram` ← `memory_capacity` (Google) or tiered (Alibaba)

### VMs (from tasks)
- `Vm.id` ← `hash(job_id, task_index)`
- `Vm.mips` ← `cpu_request × 10000`
- `Vm.ram` ← `memory_request`
- `Vm.lifetime` ← `start_time` to `end_time`

### Cloudlets (workload)
- `Cloudlet.length` ← `∫ cpu_rate × 10000 × dt`
- `Cloudlet.submitTime` ← `submit_time` or `SUBMIT` event

## Fault Labeling Strategy

### Google 2011 Fault Proxies
- **Task failures**: `event_type IN (FAIL=5, EVICT=2, KILL=3)`
- **Machine failures**: `event_type = REMOVE`, capacity reductions
- **Performance degradation**: High CPI, low cpu_rate under load

### Alibaba 2018 Fault Proxies
- **Sentinel values**: `disk_io_percent IN (-1, 101)`
- **Resource exhaustion**: `cpu_util > 95%`, `mem_util > 90%`
- **Gaps**: Missing machine_usage rows
- **Container failures**: Restarts in container_event

### Early Warning Labels
For each fault event at time `T`:
- **Positive labels**: `[T - 3600s, T]` (60-minute warning window)
- **Negative labels**: Time points > 2 hours from any fault

## Feature Engineering

### Window Aggregations (5min, 30min, 60min)

**Machine-level features**:
- `cpu_util_mean`, `cpu_util_max`, `cpu_util_std`
- `mem_util_mean`, `mem_util_std`
- `disk_io_mean`, `disk_io_anomalies` (sentinels)
- `net_in_rate`, `net_out_rate`

**Task-level features** (Google):
- `cpu_rate_mean`, `cpu_rate_volatility`
- `cpi_median`, `cpi_p95` (cycles per instruction)
- `mai_mean` (memory accesses per instruction)
- `wait_time` (SCHEDULE - SUBMIT)

**Churn indicators**:
- `machine_update_count`
- `task_eviction_rate`
- `reschedule_frequency`

## Output Formats

### 1. CloudSim JSON
```json
{
  "hosts": [
    {"id": 1, "pesNumber": 8, "mipsPerPe": 10000, "ram": 32768}
  ],
  "vms": [
    {"id": 101, "mips": 5000, "pesNumber": 2, "ram": 4096}
  ],
  "cloudlets": [
    {"id": 1001, "length": 50000, "pesNumber": 1, "submitTime": 10.0}
  ]
}
```

### 2. ML Feature Store (Parquet)
```
timestamp | machine_id | cpu_mean_5m | mem_std_30m | ... | early_fault_label
----------|------------|-------------|-------------|-----|------------------
100000    | m_12345    | 0.65        | 0.12        | ... | 0
100060    | m_12345    | 0.72        | 0.15        | ... | 1
```

### 3. Fault Events Log
```csv
machine_id,event_time,fault_type,severity,first_warning_time,lead_time_seconds
m_12345,1500000,TASK_EVICT,MEDIUM,1496400,3600
m_67890,1800000,MACHINE_REMOVE,HIGH,1795200,4800
```

## Usage in Research

1. **Baseline**: Use sample datasets (1 day) for rapid prototyping
2. **Full scale**: Run on complete traces for publication-quality results
3. **Ablation**: Compare Google-only, Alibaba-only, and combined datasets
4. **Power-aware**: Include Google 2019 PowerData for energy analysis

## References

- Google Cluster Trace format: https://github.com/google/cluster-data/blob/master/ClusterData2011_2.md
- Alibaba Trace schema: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-v2018
- CloudSim Plus entities: https://cloudsimplus.org/docs/

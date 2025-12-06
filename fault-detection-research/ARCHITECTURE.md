# System Architecture Overview

## Complete System Diagram

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                   FAULT DETECTION RESEARCH SYSTEM                         ║
║                   Multi-Modal Event Fusion (MMEF)                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: DATA SOURCES                                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────┐   │
│  │ CloudSim Plus   │  │ Google Cluster  │  │ Alibaba Cluster        │   │
│  │ Simulation      │  │ Trace           │  │ Trace                  │   │
│  │                 │  │                 │  │                        │   │
│  │ • Hosts (10)    │  │ • Workloads     │  │ • Container data       │   │
│  │ • VMs (50)      │  │ • Failures      │  │ • Resource usage       │   │
│  │ • Cloudlets     │  │ • Resources     │  │ • Failure events       │   │
│  └─────────────────┘  └─────────────────┘  └────────────────────────┘   │
│                                                                            │
│  ┌─────────────────┐  ┌──────────────────────────────────────────────┐   │
│  │ BGL System      │  │ NASA Prognostics                             │   │
│  │ Logs            │  │ Datasets                                     │   │
│  │                 │  │                                              │   │
│  │ • Error logs    │  │ • Battery degradation                        │   │
│  │ • Failures      │  │ • Turbofan engine data                       │   │
│  └─────────────────┘  └──────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Telemetry Data
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: TELEMETRY COLLECTION                                             │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                  MultiModalTelemetryCollector                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CPU    │  │  Power   │  │   Temp   │  │ Vibration│  │   Logs   │   │
│  │ Metrics  │  │ Metrics  │  │ Sensors  │  │  Sensors │  │  Parser  │   │
│  │          │  │          │  │          │  │          │  │          │   │
│  │ • Usage  │  │ • Watts  │  │ • CPU °C │  │ • Accel  │  │ • Errors │   │
│  │ • MIPS   │  │ • Current│  │ • Ambient│  │ • Freq   │  │ • Events │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │             │          │
│       └─────────────┴─────────────┴─────────────┴─────────────┘          │
│                               │                                           │
│                               ▼                                           │
│               TelemetrySnapshot (timestamp, component_data)               │
│                               │                                           │
│                               ▼                                           │
│                    TelemetryWriter (CSV/JSON)                             │
│                   output/telemetry/telemetry.csv                          │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: DATA PROCESSING & NORMALIZATION                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Raw Data → DataNormalizer → ProcessedData                                │
│                                                                            │
│  Strategies:                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │  Min-Max    │  │  Z-Score    │  │   Robust    │                      │
│  │  Scaling    │  │ Normalize   │  │  Scaling    │                      │
│  │  [0, 1]     │  │ μ=0, σ=1    │  │ IQR-based   │                      │
│  └─────────────┘  └─────────────┘  └─────────────┘                      │
│                                                                            │
│  Per-Modality Processing:                                                 │
│  CPU: [0.65, 650.2, 450.1] → [0.65, 0.65, 0.45]                          │
│  Power: [250.5] → [0.42]                                                  │
│  Temperature: [45.2, 46.8, 35.0] → [0.34, 0.39, 0.00]                    │
│  Vibration: [0.8, 85.2] → [0.60, 0.71]                                   │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: MULTI-MODAL EVENT FUSION                                         │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Input: Map<Modality, ProcessedData>                                      │
│  {                                                                         │
│    "cpu": ProcessedData([0.65, 0.65, 0.45]),                             │
│    "power": ProcessedData([0.42]),                                        │
│    "temperature": ProcessedData([0.34, 0.39, 0.00]),                     │
│    "vibration": ProcessedData([0.60, 0.71])                               │
│  }                                                                         │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │ Fusion Strategy: WeightedAverageFusion                           │     │
│  │                                                                   │     │
│  │ Weights:                                                          │     │
│  │   • CPU:         0.30                                             │     │
│  │   • Power:       0.25                                             │     │
│  │   • Temperature: 0.25                                             │     │
│  │   • Vibration:   0.20                                             │     │
│  │                                                                   │     │
│  │ Process:                                                          │     │
│  │   feature_i = Σ(weight_j × value_j)                              │     │
│  └───────────────────────────┬───────────────────────────────────────┘     │
│                              │                                             │
│                              ▼                                             │
│  Output: Unified Feature Vector                                           │
│  [0.195, 0.195, 0.135, 0.105, 0.085, 0.098, 0.00, 0.12, 0.142]          │
│   │                                                                        │
│   └─ 9 features ready for ML models                                       │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 5: ML MODEL ENSEMBLE                                                │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│              FaultDetectionEngine (Coordinator)                            │
│                          │                                                 │
│         ┌────────────────┼────────────────┬────────────┐                  │
│         │                │                │            │                  │
│         ▼                ▼                ▼            ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────────┐       │
│  │Random Forest │ │   XGBoost    │ │    LSTM    │ │ Isolation   │       │
│  │              │ │              │ │Autoencoder │ │   Forest    │       │
│  │ Supervised   │ │ Supervised   │ │Unsupervised│ │Unsupervised │       │
│  │              │ │              │ │            │ │             │       │
│  │ 200 trees    │ │ Gradient     │ │ Encoder +  │ │ 100 trees   │       │
│  │ Balanced     │ │ Boosting     │ │ Decoder    │ │ 15% contam. │       │
│  │              │ │              │ │ Recon err  │ │             │       │
│  └──────┬───────┘ └──────┬───────┘ └─────┬──────┘ └──────┬──────┘       │
│         │                │                │               │               │
│         ▼                ▼                ▼               ▼               │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │              PredictionResult (per model)                     │        │
│  │                                                                │        │
│  │  RF:   {fault: true,  confidence: 0.87, type: "FAN_FAILURE"} │        │
│  │  XGB:  {fault: true,  confidence: 0.82, type: "FAN_FAILURE"} │        │
│  │  LSTM: {fault: true,  confidence: 0.75, type: "ANOMALY"}     │        │
│  │  ISO:  {fault: false, confidence: 0.45, type: "NONE"}        │        │
│  └───────────────────────────┬──────────────────────────────────┘        │
│                              │                                             │
│                              ▼                                             │
│  ┌─────────────────────────────────────────────────────────────┐          │
│  │           VotingFaultAggregator                              │          │
│  │                                                               │          │
│  │  Majority Vote:    3/4 models say "fault"                    │          │
│  │  Avg Confidence:   (0.87 + 0.82 + 0.75) / 3 = 0.81          │          │
│  │  Fault Type:       Most voted = "FAN_FAILURE"                │          │
│  │  Component:        "COOLING_FAN"                              │          │
│  └───────────────────────────┬──────────────────────────────────┘          │
│                              │                                             │
│                              ▼                                             │
│                      DetectedFault                                         │
│  {                                                                         │
│    timestamp: 1845.0,                                                     │
│    faultType: "FAN_FAILURE",                                              │
│    component: "COOLING_FAN",                                              │
│    confidence: 0.81,                                                      │
│    severity: 0.81                                                         │
│  }                                                                         │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ LAYER 6: EVALUATION & REPORTING                                           │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  MetricsEvaluator                                                          │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────┐           │
│  │ Ground Truth Comparison                                     │           │
│  │                                                             │           │
│  │ Detected Faults vs. Injected Faults                        │           │
│  │                                                             │           │
│  │ Actual Fault: FAN_FAILURE at t=2090s                       │           │
│  │ Detected:     FAN_FAILURE at t=1845s                       │           │
│  │ Lead Time:    245 seconds ✓ Early Detection!               │           │
│  └────────────────────────────────────────────────────────────┘           │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────┐           │
│  │ Confusion Matrix                                            │           │
│  │                                                             │           │
│  │              Predicted                                      │           │
│  │              Fault   No Fault                               │           │
│  │   Actual ┌──────────┬──────────┐                           │           │
│  │   Fault  │    78    │    22    │  ← FN (Missed)            │           │
│  │          ├──────────┼──────────┤                           │           │
│  │   Normal │    12    │   288    │  ← FP (False Alarm)       │           │
│  │          └──────────┴──────────┘                           │           │
│  │             ↑          ↑                                    │           │
│  │             TP         TN                                   │           │
│  └────────────────────────────────────────────────────────────┘           │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────┐           │
│  │ EvaluationMetrics                                           │           │
│  │                                                             │           │
│  │ • Precision:     0.850  (TP / (TP + FP))                   │           │
│  │ • Recall:        0.780  (TP / (TP + FN))                   │           │
│  │ • F1-Score:      0.810  (2 × P × R / (P + R))              │           │
│  │ • Accuracy:      0.880  ((TP + TN) / Total)                │           │
│  │ • FP Rate:       0.120                                      │           │
│  │ • FN Rate:       0.220                                      │           │
│  │ • Early Detect:  245.5s avg                                 │           │
│  └────────────────────────────────────────────────────────────┘           │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────┐           │
│  │ Component-Specific Metrics                                  │           │
│  │                                                             │           │
│  │ Component      Precision   Recall    F1-Score               │           │
│  │ ──────────────────────────────────────────────              │           │
│  │ COOLING_FAN       0.880     0.820     0.849                 │           │
│  │ POWER_SUPPLY      0.850     0.760     0.803                 │           │
│  │ STORAGE_DISK      0.820     0.740     0.778                 │           │
│  │ THERMAL           0.850     0.780     0.813                 │           │
│  └────────────────────────────────────────────────────────────┘           │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: RESEARCH DELIVERABLES                                              │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  📊 Performance Report                                                     │
│  📈 Visualization Plots                                                    │
│  📝 Research Paper Draft                                                   │
│  💾 Trained ML Models                                                      │
│  📋 Deployment Recommendations                                             │
│  🔬 Reproducible Experimental Setup                                        │
└───────────────────────────────────────────────────────────────────────────┘
```

## Component Relationships

```
ResearchConfig
    ↓
DatacenterSimulation
    ├─→ TelemetryCollector
    │       ├─→ TelemetrySnapshot
    │       └─→ TelemetryWriter
    └─→ FaultInjector
            ├─→ FanFailureFault
            ├─→ PowerSupplyFault
            ├─→ DiskFailureFault
            └─→ ThermalFault

TelemetryData (CSV)
    ↓
DataNormalizer
    ↓
MultiModalFusion (MMEF)
    ├─→ WeightedAverageFusion
    └─→ LateFusion
    ↓
UnifiedFeatureVector
    ↓
FaultDetectionEngine
    ├─→ RandomForest (PythonMLBridge)
    ├─→ XGBoost (PythonMLBridge)
    ├─→ LSTMAutoencoder (PythonMLBridge)
    └─→ IsolationForest (PythonMLBridge)
    ↓
VotingFaultAggregator
    ↓
DetectedFault
    ↓
MetricsEvaluator
    ├─→ EvaluationMetrics
    ├─→ EarlyDetectionMetrics
    └─→ ComponentMetrics
```

## Data Flow Example

```
Time: t = 1845s
───────────────

Host 3 Telemetry:
  CPU:    95% → [0.95, ...]
  Power:  380W → [0.76]
  Temp:   78°C → [0.86]
  Vib:    1.5  → [0.90]

         ↓ Collection

TelemetrySnapshot:
  {
    "host-3": {
      cpu_utilization: 0.95,
      power_consumption: 380,
      temperature: 78,
      vibration: 1.5
    }
  }

         ↓ Normalization

ProcessedData:
  cpu:    [0.95]
  power:  [0.76]
  temp:   [0.86]
  vib:    [0.90]

         ↓ Fusion (MMEF)

UnifiedVector:
  [0.285, 0.190, 0.215, 0.180]

         ↓ ML Models

Predictions:
  RF:   fault=true,  conf=0.87
  XGB:  fault=true,  conf=0.82
  LSTM: fault=true,  conf=0.75
  ISO:  fault=false, conf=0.45

         ↓ Aggregation

DetectedFault:
  type: FAN_FAILURE
  component: COOLING_FAN
  confidence: 0.81
  time: 1845s

         ↓ Evaluation

Actual Failure: t=2090s
Lead Time: 245 seconds ✓
```

This architecture provides a complete, end-to-end fault detection system ready for research and deployment.

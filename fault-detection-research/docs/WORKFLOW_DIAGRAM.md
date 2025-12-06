# System Workflow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FAULT DETECTION RESEARCH PIPELINE                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA COLLECTION                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐         ┌──────────────────┐                    │
│  │  CloudSim Plus   │         │  External        │                    │
│  │  Simulation      │         │  Datasets        │                    │
│  │                  │         │  - Google        │                    │
│  │  - Datacenter    │         │  - Alibaba       │                    │
│  │  - Hosts/VMs     │         │  - BGL Logs      │                    │
│  │  - Workloads     │         │  - NASA          │                    │
│  └────────┬─────────┘         └────────┬─────────┘                    │
│           │                            │                               │
│           ├────────────────────────────┤                               │
│           │                            │                               │
│           ▼                            ▼                               │
│  ┌─────────────────────────────────────────────┐                      │
│  │   Telemetry Collectors                      │                      │
│  │   - CPU metrics                             │                      │
│  │   - Power consumption                       │                      │
│  │   - Temperature sensors                     │                      │
│  │   - Vibration data                          │                      │
│  │   - System logs                             │                      │
│  └─────────────────┬───────────────────────────┘                      │
│                    │                                                   │
│                    ▼                                                   │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Raw Telemetry Data (CSV/Prometheus)        │                      │
│  └─────────────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: DATA PROCESSING & NORMALIZATION                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Data Preprocessing                         │                      │
│  │  - Time alignment                           │                      │
│  │  - Missing value handling                   │                      │
│  │  - Outlier detection                        │                      │
│  │  - Feature extraction                       │                      │
│  └─────────────────┬───────────────────────────┘                      │
│                    │                                                   │
│                    ▼                                                   │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Data Normalization                         │                      │
│  │  - Min-Max scaling                          │                      │
│  │  - Z-score standardization                  │                      │
│  │  - Robust scaling                           │                      │
│  └─────────────────┬───────────────────────────┘                      │
│                    │                                                   │
│                    ▼                                                   │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Processed Data per Modality                │                      │
│  │  [CPU] [Power] [Temp] [Vibration] [Logs]   │                      │
│  └─────────────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: MULTI-MODAL EVENT FUSION (MMEF)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│      [CPU Data]    [Power Data]   [Temp Data]   [Vibration]  [Logs]   │
│           │              │              │             │          │      │
│           ├──────────────┼──────────────┼─────────────┼──────────┤      │
│           │              │              │             │          │      │
│           ▼              ▼              ▼             ▼          ▼      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Multi-Modal Fusion Strategy                         │  │
│  │                                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │  │
│  │  │  Weighted    │  │  Attention   │  │  Late Fusion         │  │  │
│  │  │  Average     │  │  Mechanism   │  │  (Concatenation)     │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │  │
│  │                                                                  │  │
│  └────────────────────────────┬─────────────────────────────────────┘  │
│                               │                                        │
│                               ▼                                        │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Unified Feature Vector                     │                      │
│  │  [f1, f2, f3, ..., fn]                      │                      │
│  └─────────────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: ML MODEL INFERENCE                                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐             │
│  │ Random Forest │  │   XGBoost     │  │     LSTM      │             │
│  │  Classifier   │  │  Classifier   │  │  Autoencoder  │             │
│  │               │  │               │  │  (Anomaly)    │             │
│  │  Supervised   │  │  Supervised   │  │  Unsupervised │             │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘             │
│          │                  │                  │                      │
│          │                  │                  │                      │
│  ┌───────────────────────────────────────────────┐                    │
│  │         Isolation Forest                      │                    │
│  │         (Anomaly Detection)                   │                    │
│  │         Unsupervised                          │                    │
│  └─────────────────┬─────────────────────────────┘                    │
│                    │                                                   │
│          ┌─────────┴──────────┬──────────────┬──────────┐            │
│          ▼                    ▼              ▼          ▼            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │ Prediction  │  │ Prediction   │  │ Prediction  │  │Prediction│  │
│  │   Result    │  │   Result     │  │   Result    │  │  Result  │  │
│  └─────────────┘  └──────────────┘  └─────────────┘  └──────────┘  │
│          │                    │              │          │            │
│          └────────────────────┴──────────────┴──────────┘            │
│                               │                                       │
│                               ▼                                       │
│  ┌─────────────────────────────────────────────┐                     │
│  │  Voting Aggregator                          │                     │
│  │  - Majority voting                          │                     │
│  │  - Confidence weighting                     │                     │
│  │  - Component-level classification           │                     │
│  └─────────────────┬───────────────────────────┘                     │
└────────────────────┼─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: FAULT ALERT & EVALUATION                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Fault Detection Result                     │                      │
│  │                                             │                      │
│  │  • Fault Type: [FAN_FAILURE]                │                      │
│  │  • Component:  [COOLING_FAN]                │                      │
│  │  • Confidence: 0.87                         │                      │
│  │  • Severity:   HIGH                         │                      │
│  │  • Timestamp:  1234567890                   │                      │
│  │  • Lead Time:  245 seconds before failure   │                      │
│  └─────────────────┬───────────────────────────┘                      │
│                    │                                                   │
│                    ▼                                                   │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Performance Metrics                        │                      │
│  │                                             │                      │
│  │  • Precision:     0.85                      │                      │
│  │  • Recall:        0.78                      │                      │
│  │  • F1-Score:      0.81                      │                      │
│  │  • Early Detection: 245.5 seconds avg       │                      │
│  │                                             │                      │
│  │  Component Breakdown:                       │                      │
│  │  • Fan:          P=0.88  R=0.82             │                      │
│  │  • Power Supply: P=0.85  R=0.76             │                      │
│  │  • Disk:         P=0.82  R=0.74             │                      │
│  └─────────────────────────────────────────────┘                      │
│                                                                         │
│  ┌─────────────────────────────────────────────┐                      │
│  │  Research Report & Deployment Strategy      │                      │
│  │  - Model performance analysis               │                      │
│  │  - Datacenter deployment recommendations    │                      │
│  │  - Cost-benefit analysis                    │                      │
│  └─────────────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│CloudSim  │─────▶│Telemetry │─────▶│   Data   │─────▶│  MMEF    │
│          │      │Collector │      │Processor │      │  Fusion  │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
                                                             │
                                                             ▼
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Research │◀─────│Evaluation│◀─────│  Fault   │◀─────│   ML     │
│  Report  │      │  Engine  │      │Aggregator│      │ Models   │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

## Data Flow Timeline

```
T0: Simulation Start
│
├─ T1: First telemetry collection (1s)
│   └─ Collect: CPU, Power, Temp, Vibration
│
├─ T2-T1799: Normal operation (no faults)
│   └─ Continuous telemetry collection
│
├─ T1800: Fault injection begins
│   ├─ Inject: FAN_FAILURE on Host 3
│   ├─ Inject: THERMAL_ISSUE on Host 7
│   └─ Effects: Temperature ↑, Vibration ↑
│
├─ T1805-T2100: Early warning period
│   ├─ ML models detect anomalies
│   ├─ Confidence builds over time
│   └─ Alert issued at T1845 (245s before failure)
│
├─ T2100: Actual hardware failure
│   └─ Host 3 cooling system failure
│
└─ T3600: Simulation end
    └─ Evaluation & metrics calculation
```

This workflow ensures a systematic approach to fault detection research, from data collection through evaluation and deployment planning.

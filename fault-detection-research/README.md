# AI/ML Driven Fault Detection Research Project

## Overview

This project implements and evaluates an AI/ML-driven fault detection system using **Multi-Modal Event Fusion (MMEF)** combined with telemetry data for predictive hardware fault detection in cloud datacenters.

## Research Objectives

The system will:
- Collect open-source telemetry data representing hardware conditions (temperature, power usage, vibration, system logs)
- Process and normalize the data to create a unified dataset
- Train supervised and unsupervised machine learning models (Random Forest, XGBoost, LSTM autoencoders, Isolation Forest) to predict upcoming hardware faults
- Evaluate results and the model's precision, recall, and how early it detects a failure before it occurs

## Architecture

```
Data Collection → Processing → Multi-Modal Fusion → AI/ML Inference → Fault Alert
```

### Components

1. **Data Collection Layer**
   - Telemetry collectors for temperature, power, vibration
   - System log parsers
   - Integration with Prometheus Node Exporter format

2. **Data Processing & Normalization**
   - Time-series alignment
   - Feature extraction
   - Data cleaning and normalization

3. **Multi-Modal Event Fusion (MMEF)**
   - Combines heterogeneous data sources
   - Temporal correlation analysis
   - Feature fusion strategies

4. **ML Model Pipeline**
   - **Supervised Models**: Random Forest, XGBoost
   - **Unsupervised Models**: Isolation Forest, LSTM Autoencoders
   - Model training and inference engines

5. **Fault Detection & Evaluation**
   - Component-level fault classification (fan, power supply, disk)
   - Early warning system
   - Performance metrics (precision, recall, F1, early detection time)

## Experimental Setup

### Simulation Tools
- **CloudSim Plus**: Simulating workloads, VM allocation, and hardware behavior

### Telemetry Data Collection
- Logs and metrics generated with Prometheus Node Exporter format
- Custom telemetry generators for missing data types

### Data Sources
- Google Cluster Trace
- Alibaba Cluster Trace
- BGL System Logs
- NASA Prognostics Datasets (power usage behavior)

### Output
- Fault likelihood per component (fan, power supply, disk)
- Early warning classifications
- Probable error cause analysis

## Project Structure

```
fault-detection-research/
├── src/main/java/org/faultdetection/
│   ├── core/                    # Core framework classes
│   ├── telemetry/               # Data collection modules
│   ├── processing/              # Data processing & normalization
│   ├── fusion/                  # Multi-Modal Event Fusion
│   ├── ml/                      # ML model interfaces & adapters
│   ├── detection/               # Fault detection engine
│   ├── evaluation/              # Metrics & evaluation
│   ├── datasources/             # Dataset connectors
│   ├── simulation/              # CloudSim integration
│   └── config/                  # Configuration management
├── src/main/resources/
│   ├── datasets/                # Sample datasets
│   ├── config/                  # Configuration files
│   └── models/                  # Pre-trained model configs
├── python/                      # Python ML training scripts
│   ├── models/                  # ML model implementations
│   ├── training/                # Training pipelines
│   └── evaluation/              # Evaluation scripts
└── docs/                        # Documentation & research notes
```

## Usage

### 1. Build the Project

```bash
cd fault-detection-research
mvn clean install
```

### 2. Run Telemetry Collection Simulation

```bash
mvn exec:java -Dexec.mainClass="org.faultdetection.simulation.TelemetrySimulation"
```

### 3. Train ML Models (Python)

```bash
cd python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python training/train_all_models.py
```

### 4. Run Fault Detection Evaluation

```bash
mvn exec:java -Dexec.mainClass="org.faultdetection.FaultDetectionResearchMain"
```

## Research Deliverables

1. **Replicable Pipeline**: Complete end-to-end pipeline using free and open-source resources
2. **Performance Analysis**: Detailed analysis of model performance metrics
3. **Deployment Strategies**: Recommendations for datacenter deployment
4. **Research Report**: Comprehensive documentation of methodology and findings

## License

This is a research project. Please cite appropriately if used in academic work.

## Contact

For questions and collaboration opportunities, please open an issue in the repository.

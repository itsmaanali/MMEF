# Fault Detection Research - Quick Start Guide

This guide will help you get started with the AI/ML-driven fault detection research project.

## Prerequisites

- Java 17 or higher
- Python 3.8 or higher
- Maven 3.6 or higher
- At least 8GB RAM
- 50GB free disk space

## Installation

### 1. Build the Project

```bash
cd fault-detection-research
mvn clean install
```

### 2. Setup Python Environment

```bash
cd python
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Basic Scenario

### Step 1: Run CloudSim Simulation

This generates telemetry data with injected faults:

```bash
mvn exec:java -Dexec.mainClass="org.faultdetection.scenarios.BasicFaultDetectionScenario"
```

Expected output:
- Telemetry CSV file in `output/telemetry/telemetry.csv`
- Console logs showing simulation progress
- Approximately 600 seconds (10 minutes) of simulated time

### Step 2: Train ML Models

```bash
cd python
python training/train_all_models.py \
    --data ../output/telemetry/telemetry.csv \
    --output ../models
```

This will train:
1. Random Forest classifier
2. XGBoost classifier
3. LSTM Autoencoder
4. Isolation Forest

Training takes ~5-10 minutes depending on your hardware.

### Step 3: Run Fault Detection

```bash
cd ..
mvn exec:java -Dexec.mainClass="org.faultdetection.FaultDetectionResearchMain"
```

This will:
- Load the trained models
- Process telemetry data
- Apply multi-modal fusion
- Detect faults
- Generate evaluation metrics

### Step 4: View Results

Results are saved in:
- `output/research-results/` - Detection results and metrics
- `output/logs/` - Detailed execution logs

## Example Output

```
================================================================================
FAULT DETECTION EVALUATION RESULTS
================================================================================
Precision:                    0.850
Recall:                       0.780
F1 Score:                     0.810
Accuracy:                     0.880
False Positive Rate:          0.120
False Negative Rate:          0.220
Average Early Detection Time: 245.5 seconds

Confusion Matrix:
  True Positives:  78
  False Positives: 12
  True Negatives:  288
  False Negatives: 22
================================================================================
```

## Advanced Usage

### Custom Configuration

Edit `src/main/resources/config.json` to customize:
- Number of hosts and VMs
- Fault injection parameters
- ML model settings
- Fusion strategies

### Large-Scale Scenario

Run a large datacenter simulation:

```bash
mvn exec:java -Dexec.mainClass="org.faultdetection.scenarios.LargeScaleDatacenterScenario"
```

This simulates:
- 100 physical hosts
- 500 VMs
- 2 hours of operation
- Multiple concurrent faults

### Using External Datasets

1. Download datasets (see [docs/DATASET_GUIDE.md](docs/DATASET_GUIDE.md))
2. Place in `datasets/` directory
3. Run preprocessing:

```bash
cd python/preprocessing
python preprocess_all_datasets.py
```

## Project Structure

```
fault-detection-research/
├── src/main/java/org/faultdetection/
│   ├── core/              # Core framework
│   ├── telemetry/         # Data collection
│   ├── processing/        # Data processing
│   ├── fusion/            # Multi-modal fusion
│   ├── ml/                # ML model interfaces
│   ├── detection/         # Fault detection engine
│   ├── evaluation/        # Metrics and evaluation
│   └── scenarios/         # Example scenarios
├── python/
│   ├── models/            # ML model trainers
│   ├── training/          # Training scripts
│   └── inference/         # Inference scripts
├── docs/                  # Documentation
├── output/                # Generated data and results
└── models/                # Trained ML models
```

## Troubleshooting

### Out of Memory Error

Increase JVM heap size:

```bash
export MAVEN_OPTS="-Xmx4g"
mvn exec:java ...
```

### Python Package Errors

Ensure you're using the virtual environment:

```bash
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### No Models Found

Make sure you've run the training step before fault detection:

```bash
cd python
python training/train_all_models.py --data ../output/telemetry/telemetry.csv --output ../models
```

## Next Steps

1. **Experiment with parameters**: Modify simulation settings to see how they affect detection performance
2. **Try different fusion strategies**: Change the fusion strategy in config.json
3. **Add custom fault types**: Extend the fault injection system
4. **Integrate real datasets**: Use Google Cluster Trace or Alibaba datasets
5. **Optimize models**: Tune ML model hyperparameters for better performance

## Getting Help

- Check [README.md](README.md) for detailed documentation
- Review [docs/WORKFLOW_DIAGRAM.md](docs/WORKFLOW_DIAGRAM.md) for system architecture
- See [docs/DATASET_GUIDE.md](docs/DATASET_GUIDE.md) for dataset information
- Open an issue on GitHub for bugs or questions

## Citation

If you use this research project in your work, please cite:

```bibtex
@misc{faultdetection2024,
  title={AI/ML-Driven Fault Detection Using Multi-Modal Event Fusion},
  author={Your Name},
  year={2024},
  howpublished={\\url{https://github.com/yourusername/fault-detection-research}}
}
```

Happy researching!

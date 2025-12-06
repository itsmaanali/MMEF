package org.faultdetection.detection;

import org.faultdetection.config.ResearchConfig;
import org.faultdetection.ml.FaultPredictionModel;
import org.faultdetection.ml.PredictionResult;
import org.faultdetection.ml.models.PythonMLBridge;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;
import java.util.*;

/**
 * Main fault detection engine that coordinates multiple ML models
 * and produces final fault predictions.
 */
public class FaultDetectionEngine {
    private static final Logger logger = LoggerFactory.getLogger(FaultDetectionEngine.class);

    private final ResearchConfig config;
    private final Map<String, FaultPredictionModel> models;
    private final FaultAggregator aggregator;

    public FaultDetectionEngine(ResearchConfig config) {
        this.config = config;
        this.models = new HashMap<>();
        this.aggregator = new VotingFaultAggregator();
    }

    /**
     * Load and initialize all configured ML models.
     */
    public void loadModels() throws Exception {
        logger.info("Loading ML models...");

        Path modelsDir = Path.of(config.getModelsDirectory());

        if (config.isUseRandomForest()) {
            FaultPredictionModel rf = new PythonMLBridge("RandomForest");
            rf.initialize(Map.of(
                "pythonScript", "python/inference/random_forest.py",
                "confidenceThreshold", config.getConfidenceThreshold()
            ));
            rf.loadModel(modelsDir.resolve("random_forest.pkl"));
            models.put("RandomForest", rf);
            logger.info("Loaded RandomForest model");
        }

        if (config.isUseXGBoost()) {
            FaultPredictionModel xgb = new PythonMLBridge("XGBoost");
            xgb.initialize(Map.of(
                "pythonScript", "python/inference/xgboost.py",
                "confidenceThreshold", config.getConfidenceThreshold()
            ));
            xgb.loadModel(modelsDir.resolve("xgboost.pkl"));
            models.put("XGBoost", xgb);
            logger.info("Loaded XGBoost model");
        }

        if (config.isUseLSTMAutoencoder()) {
            FaultPredictionModel lstm = new PythonMLBridge("LSTM_Autoencoder");
            lstm.initialize(Map.of(
                "pythonScript", "python/inference/lstm_autoencoder.py",
                "confidenceThreshold", config.getConfidenceThreshold()
            ));
            lstm.loadModel(modelsDir.resolve("lstm_autoencoder.h5"));
            models.put("LSTM_Autoencoder", lstm);
            logger.info("Loaded LSTM Autoencoder model");
        }

        if (config.isUseIsolationForest()) {
            FaultPredictionModel isoForest = new PythonMLBridge("IsolationForest");
            isoForest.initialize(Map.of(
                "pythonScript", "python/inference/isolation_forest.py",
                "confidenceThreshold", config.getConfidenceThreshold()
            ));
            isoForest.loadModel(modelsDir.resolve("isolation_forest.pkl"));
            models.put("IsolationForest", isoForest);
            logger.info("Loaded Isolation Forest model");
        }

        logger.info("Successfully loaded {} models", models.size());
    }

    /**
     * Detect faults from telemetry data.
     * Returns a list of detected faults with timestamps and confidence.
     */
    public List<DetectedFault> detectFaults(Path telemetryDataPath) throws Exception {
        logger.info("Running fault detection on: {}", telemetryDataPath);

        // In a real implementation:
        // 1. Read telemetry CSV
        // 2. Process and normalize data
        // 3. Apply multi-modal fusion
        // 4. Run each model
        // 5. Aggregate results
        // 6. Return detected faults

        List<DetectedFault> detectedFaults = new ArrayList<>();

        // Placeholder: simulate detection
        logger.info("Fault detection completed. Found {} faults", detectedFaults.size());

        return detectedFaults;
    }

    /**
     * Run real-time fault detection on a single data point.
     */
    public DetectedFault detectFaultRealtime(double[] features, double timestamp) {
        Map<String, PredictionResult> modelPredictions = new HashMap<>();

        // Get prediction from each model
        for (Map.Entry<String, FaultPredictionModel> entry : models.entrySet()) {
            String modelName = entry.getKey();
            FaultPredictionModel model = entry.getValue();

            if (model.isReady()) {
                PredictionResult result = model.predict(features);
                modelPredictions.put(modelName, result);
            }
        }

        // Aggregate predictions
        return aggregator.aggregate(modelPredictions, timestamp);
    }

    public Map<String, FaultPredictionModel> getModels() {
        return models;
    }
}

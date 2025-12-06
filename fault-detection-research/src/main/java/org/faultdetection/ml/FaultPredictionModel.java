package org.faultdetection.ml;

import java.nio.file.Path;
import java.util.Map;

/**
 * Interface for fault prediction ML models.
 * Supports both supervised and unsupervised learning approaches.
 */
public interface FaultPredictionModel {

    /**
     * Initialize the model with configuration parameters.
     */
    void initialize(Map<String, Object> config);

    /**
     * Load a pre-trained model from disk.
     */
    void loadModel(Path modelPath) throws Exception;

    /**
     * Make a prediction on input features.
     *
     * @param features Input feature vector
     * @return Prediction result containing fault probability, type, etc.
     */
    PredictionResult predict(double[] features);

    /**
     * Batch prediction on multiple feature vectors.
     */
    PredictionResult[] predictBatch(double[][] features);

    /**
     * Get the model type/name.
     */
    String getModelType();

    /**
     * Get the model's confidence threshold for positive predictions.
     */
    double getConfidenceThreshold();

    /**
     * Set the confidence threshold.
     */
    void setConfidenceThreshold(double threshold);

    /**
     * Check if the model is ready for predictions.
     */
    boolean isReady();
}

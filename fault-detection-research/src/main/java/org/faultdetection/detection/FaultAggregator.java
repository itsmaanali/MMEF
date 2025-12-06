package org.faultdetection.detection;

import org.faultdetection.ml.PredictionResult;

import java.util.Map;

/**
 * Interface for aggregating predictions from multiple ML models.
 */
public interface FaultAggregator {

    /**
     * Aggregate predictions from multiple models into a single fault detection result.
     *
     * @param modelPredictions Map of model name to prediction result
     * @param timestamp Current timestamp
     * @return Aggregated fault detection result
     */
    DetectedFault aggregate(Map<String, PredictionResult> modelPredictions, double timestamp);
}

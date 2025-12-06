package org.faultdetection.fusion;

import org.faultdetection.processing.ProcessedData;

import java.util.List;
import java.util.Map;

/**
 * Interface for Multi-Modal Event Fusion (MMEF) strategies.
 * Combines data from multiple modalities (CPU, power, temperature, vibration, logs)
 * into a unified representation for ML models.
 */
public interface MultiModalFusion {

    /**
     * Fuse data from multiple modalities into a unified feature vector.
     *
     * @param modalityData Map of modality name to processed data
     * @return Fused feature vector
     */
    double[] fuse(Map<String, ProcessedData> modalityData);

    /**
     * Get the dimensionality of the fused output.
     */
    int getOutputDimension();

    /**
     * Get the strategy name.
     */
    String getStrategyName();

    /**
     * Initialize the fusion strategy with configuration.
     */
    void initialize(Map<String, Object> config);
}

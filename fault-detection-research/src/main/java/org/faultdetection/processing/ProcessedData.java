package org.faultdetection.processing;

import java.util.HashMap;
import java.util.Map;

/**
 * Represents processed and normalized data ready for fusion and ML inference.
 */
public class ProcessedData {
    private final String modalityType;
    private final double[] features;
    private final Map<String, Object> metadata;
    private final double timestamp;

    public ProcessedData(String modalityType, double[] features, double timestamp) {
        this.modalityType = modalityType;
        this.features = features;
        this.timestamp = timestamp;
        this.metadata = new HashMap<>();
    }

    public String getModalityType() {
        return modalityType;
    }

    public double[] getFeatures() {
        return features;
    }

    public double getTimestamp() {
        return timestamp;
    }

    public Map<String, Object> getMetadata() {
        return metadata;
    }

    public void addMetadata(String key, Object value) {
        metadata.put(key, value);
    }
}

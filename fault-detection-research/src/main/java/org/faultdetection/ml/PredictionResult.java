package org.faultdetection.ml;

import java.util.HashMap;
import java.util.Map;

/**
 * Represents the result of a fault prediction.
 */
public class PredictionResult {
    private final boolean isFault;
    private final double confidence;
    private final String predictedFaultType;
    private final String affectedComponent;
    private final Map<String, Double> componentProbabilities;
    private final double timestamp;

    private PredictionResult(Builder builder) {
        this.isFault = builder.isFault;
        this.confidence = builder.confidence;
        this.predictedFaultType = builder.predictedFaultType;
        this.affectedComponent = builder.affectedComponent;
        this.componentProbabilities = builder.componentProbabilities;
        this.timestamp = builder.timestamp;
    }

    public boolean isFault() {
        return isFault;
    }

    public double getConfidence() {
        return confidence;
    }

    public String getPredictedFaultType() {
        return predictedFaultType;
    }

    public String getAffectedComponent() {
        return affectedComponent;
    }

    public Map<String, Double> getComponentProbabilities() {
        return componentProbabilities;
    }

    public double getTimestamp() {
        return timestamp;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private boolean isFault = false;
        private double confidence = 0.0;
        private String predictedFaultType = "NONE";
        private String affectedComponent = "UNKNOWN";
        private Map<String, Double> componentProbabilities = new HashMap<>();
        private double timestamp = 0.0;

        public Builder isFault(boolean isFault) {
            this.isFault = isFault;
            return this;
        }

        public Builder confidence(double confidence) {
            this.confidence = confidence;
            return this;
        }

        public Builder predictedFaultType(String faultType) {
            this.predictedFaultType = faultType;
            return this;
        }

        public Builder affectedComponent(String component) {
            this.affectedComponent = component;
            return this;
        }

        public Builder componentProbability(String component, double probability) {
            this.componentProbabilities.put(component, probability);
            return this;
        }

        public Builder timestamp(double timestamp) {
            this.timestamp = timestamp;
            return this;
        }

        public PredictionResult build() {
            return new PredictionResult(this);
        }
    }

    @Override
    public String toString() {
        return String.format("PredictionResult{fault=%b, confidence=%.3f, type=%s, component=%s}",
            isFault, confidence, predictedFaultType, affectedComponent);
    }
}

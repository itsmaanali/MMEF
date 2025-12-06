package org.faultdetection.detection;

import java.util.HashMap;
import java.util.Map;

/**
 * Represents a detected fault with all relevant information.
 */
public class DetectedFault {
    private final double timestamp;
    private final String faultType;
    private final String affectedComponent;
    private final double confidence;
    private final Map<String, Double> modelVotes;
    private final double severity;

    private DetectedFault(Builder builder) {
        this.timestamp = builder.timestamp;
        this.faultType = builder.faultType;
        this.affectedComponent = builder.affectedComponent;
        this.confidence = builder.confidence;
        this.modelVotes = builder.modelVotes;
        this.severity = builder.severity;
    }

    public double getTimestamp() {
        return timestamp;
    }

    public String getFaultType() {
        return faultType;
    }

    public String getAffectedComponent() {
        return affectedComponent;
    }

    public double getConfidence() {
        return confidence;
    }

    public Map<String, Double> getModelVotes() {
        return modelVotes;
    }

    public double getSeverity() {
        return severity;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private double timestamp = 0.0;
        private String faultType = "UNKNOWN";
        private String affectedComponent = "UNKNOWN";
        private double confidence = 0.0;
        private Map<String, Double> modelVotes = new HashMap<>();
        private double severity = 0.5;

        public Builder timestamp(double timestamp) {
            this.timestamp = timestamp;
            return this;
        }

        public Builder faultType(String faultType) {
            this.faultType = faultType;
            return this;
        }

        public Builder affectedComponent(String component) {
            this.affectedComponent = component;
            return this;
        }

        public Builder confidence(double confidence) {
            this.confidence = confidence;
            return this;
        }

        public Builder modelVote(String modelName, double vote) {
            this.modelVotes.put(modelName, vote);
            return this;
        }

        public Builder severity(double severity) {
            this.severity = severity;
            return this;
        }

        public DetectedFault build() {
            return new DetectedFault(this);
        }
    }

    @Override
    public String toString() {
        return String.format("DetectedFault{time=%.1f, type=%s, component=%s, confidence=%.3f, severity=%.2f}",
            timestamp, faultType, affectedComponent, confidence, severity);
    }
}

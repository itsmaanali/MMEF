package org.faultdetection.evaluation;

import java.util.ArrayList;
import java.util.List;

/**
 * Metrics for early fault detection capability.
 */
public class EarlyDetectionMetrics {
    private final List<Double> detectionLeadTimes;
    private final List<Double> detectionConfidences;
    private int missedFaults;

    public EarlyDetectionMetrics() {
        this.detectionLeadTimes = new ArrayList<>();
        this.detectionConfidences = new ArrayList<>();
        this.missedFaults = 0;
    }

    public void addDetection(double leadTime, double confidence) {
        detectionLeadTimes.add(leadTime);
        detectionConfidences.add(confidence);
    }

    public void recordMissedFault() {
        missedFaults++;
    }

    public double getAverageLeadTime() {
        return detectionLeadTimes.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElse(0.0);
    }

    public double getMinLeadTime() {
        return detectionLeadTimes.stream()
            .mapToDouble(Double::doubleValue)
            .min()
            .orElse(0.0);
    }

    public double getMaxLeadTime() {
        return detectionLeadTimes.stream()
            .mapToDouble(Double::doubleValue)
            .max()
            .orElse(0.0);
    }

    public double getAverageConfidence() {
        return detectionConfidences.stream()
            .mapToDouble(Double::doubleValue)
            .average()
            .orElse(0.0);
    }

    public int getTotalDetections() {
        return detectionLeadTimes.size();
    }

    public int getMissedFaults() {
        return missedFaults;
    }

    public double getDetectionRate() {
        int total = getTotalDetections() + missedFaults;
        return total > 0 ? (double) getTotalDetections() / total : 0.0;
    }
}

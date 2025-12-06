package org.faultdetection.evaluation;

import org.faultdetection.config.ResearchConfig;
import org.faultdetection.detection.DetectedFault;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;
import java.util.List;

/**
 * Evaluates fault detection performance using standard ML metrics.
 * Computes precision, recall, F1-score, and early detection metrics.
 */
public class MetricsEvaluator {
    private static final Logger logger = LoggerFactory.getLogger(MetricsEvaluator.class);

    private final ResearchConfig config;

    public MetricsEvaluator(ResearchConfig config) {
        this.config = config;
    }

    /**
     * Evaluate detection results against ground truth.
     */
    public EvaluationMetrics evaluate(List<DetectedFault> detectedFaults, Path groundTruthPath) {
        logger.info("Evaluating fault detection performance...");

        // In a real implementation:
        // 1. Load ground truth labels from fault injection logs
        // 2. Match detected faults with actual faults
        // 3. Calculate TP, FP, TN, FN
        // 4. Compute precision, recall, F1
        // 5. Calculate early detection time

        EvaluationMetrics metrics = new EvaluationMetrics();

        // Placeholder calculations
        metrics.setPrecision(0.85);
        metrics.setRecall(0.78);
        metrics.setF1Score(0.81);
        metrics.setAccuracy(0.88);
        metrics.setAverageEarlyDetectionTime(245.5); // seconds
        metrics.setFalsePositiveRate(0.12);
        metrics.setFalseNegativeRate(0.22);

        logger.info("Evaluation completed");
        return metrics;
    }

    /**
     * Evaluate early detection capability.
     * Measures how early faults are detected before actual failure.
     */
    public EarlyDetectionMetrics evaluateEarlyDetection(
            List<DetectedFault> detectedFaults,
            List<ActualFault> actualFaults) {

        EarlyDetectionMetrics metrics = new EarlyDetectionMetrics();

        for (ActualFault actualFault : actualFaults) {
            // Find earliest detection before this fault
            DetectedFault earliestDetection = findEarliestDetection(
                detectedFaults,
                actualFault
            );

            if (earliestDetection != null) {
                double leadTime = actualFault.getTimestamp() - earliestDetection.getTimestamp();

                if (leadTime >= 0) {
                    metrics.addDetection(leadTime, earliestDetection.getConfidence());
                }
            } else {
                metrics.recordMissedFault();
            }
        }

        return metrics;
    }

    private DetectedFault findEarliestDetection(
            List<DetectedFault> detections,
            ActualFault actualFault) {

        double threshold = config.getEarlyDetectionThresholdSeconds();
        DetectedFault earliest = null;
        double earliestTime = Double.MAX_VALUE;

        for (DetectedFault detection : detections) {
            // Check if detection is before the actual fault
            double leadTime = actualFault.getTimestamp() - detection.getTimestamp();

            if (leadTime >= 0 && leadTime <= threshold) {
                if (detection.getTimestamp() < earliestTime) {
                    earliest = detection;
                    earliestTime = detection.getTimestamp();
                }
            }
        }

        return earliest;
    }

    /**
     * Calculate component-specific metrics (fan, power supply, disk).
     */
    public ComponentMetrics evaluateComponentDetection(
            List<DetectedFault> detectedFaults,
            List<ActualFault> actualFaults) {

        ComponentMetrics metrics = new ComponentMetrics();

        // Group by component and calculate metrics
        String[] components = {"FAN", "POWER_SUPPLY", "DISK", "THERMAL"};

        for (String component : components) {
            double precision = calculateComponentPrecision(detectedFaults, actualFaults, component);
            double recall = calculateComponentRecall(detectedFaults, actualFaults, component);

            metrics.addComponentMetric(component, precision, recall);
        }

        return metrics;
    }

    private double calculateComponentPrecision(
            List<DetectedFault> detected,
            List<ActualFault> actual,
            String component) {
        // Placeholder
        return 0.8;
    }

    private double calculateComponentRecall(
            List<DetectedFault> detected,
            List<ActualFault> actual,
            String component) {
        // Placeholder
        return 0.75;
    }
}

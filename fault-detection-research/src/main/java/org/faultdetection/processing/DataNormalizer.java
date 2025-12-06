package org.faultdetection.processing;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

/**
 * Normalizes telemetry data using various strategies (min-max, z-score, etc.).
 * Essential for preparing multi-modal data for ML models.
 */
public class DataNormalizer {
    private static final Logger logger = LoggerFactory.getLogger(DataNormalizer.class);

    private final NormalizationStrategy strategy;
    private final Map<String, Statistics> featureStats;

    public enum NormalizationStrategy {
        MIN_MAX,    // Scale to [0, 1]
        Z_SCORE,    // Standardize to mean=0, std=1
        ROBUST,     // Use median and IQR (robust to outliers)
        NONE        // No normalization
    }

    public DataNormalizer(NormalizationStrategy strategy) {
        this.strategy = strategy;
        this.featureStats = new HashMap<>();
    }

    /**
     * Fit the normalizer on training data to compute statistics.
     */
    public void fit(String featureName, double[] data) {
        Statistics stats = computeStatistics(data);
        featureStats.put(featureName, stats);
        logger.debug("Fitted normalizer for feature '{}': {}", featureName, stats);
    }

    /**
     * Transform a single value using fitted statistics.
     */
    public double transform(String featureName, double value) {
        if (!featureStats.containsKey(featureName)) {
            logger.warn("No statistics for feature '{}', returning raw value", featureName);
            return value;
        }

        Statistics stats = featureStats.get(featureName);

        return switch (strategy) {
            case MIN_MAX -> normalizeMinMax(value, stats);
            case Z_SCORE -> normalizeZScore(value, stats);
            case ROBUST -> normalizeRobust(value, stats);
            case NONE -> value;
        };
    }

    /**
     * Transform an array of values.
     */
    public double[] transform(String featureName, double[] values) {
        double[] normalized = new double[values.length];
        for (int i = 0; i < values.length; i++) {
            normalized[i] = transform(featureName, values[i]);
        }
        return normalized;
    }

    private double normalizeMinMax(double value, Statistics stats) {
        if (stats.max == stats.min) return 0.5; // Handle constant values
        return (value - stats.min) / (stats.max - stats.min);
    }

    private double normalizeZScore(double value, Statistics stats) {
        if (stats.stdDev == 0) return 0.0; // Handle zero variance
        return (value - stats.mean) / stats.stdDev;
    }

    private double normalizeRobust(double value, Statistics stats) {
        if (stats.iqr == 0) return 0.0;
        return (value - stats.median) / stats.iqr;
    }

    private Statistics computeStatistics(double[] data) {
        Statistics stats = new Statistics();

        // Compute basic statistics
        double sum = 0;
        stats.min = Double.MAX_VALUE;
        stats.max = Double.MIN_VALUE;

        for (double value : data) {
            sum += value;
            stats.min = Math.min(stats.min, value);
            stats.max = Math.max(stats.max, value);
        }

        stats.mean = sum / data.length;

        // Compute standard deviation
        double sumSquaredDiff = 0;
        for (double value : data) {
            sumSquaredDiff += Math.pow(value - stats.mean, 2);
        }
        stats.stdDev = Math.sqrt(sumSquaredDiff / data.length);

        // Compute median and IQR (simplified)
        double[] sorted = data.clone();
        java.util.Arrays.sort(sorted);
        stats.median = sorted[sorted.length / 2];

        int q1Index = sorted.length / 4;
        int q3Index = 3 * sorted.length / 4;
        stats.iqr = sorted[q3Index] - sorted[q1Index];

        return stats;
    }

    public NormalizationStrategy getStrategy() {
        return strategy;
    }

    private static class Statistics {
        double min;
        double max;
        double mean;
        double median;
        double stdDev;
        double iqr;

        @Override
        public String toString() {
            return String.format("Stats{min=%.2f, max=%.2f, mean=%.2f, std=%.2f}",
                min, max, mean, stdDev);
        }
    }
}

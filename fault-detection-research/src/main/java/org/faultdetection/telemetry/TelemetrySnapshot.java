package org.faultdetection.telemetry;

import java.util.HashMap;
import java.util.Map;

/**
 * Represents a snapshot of telemetry data at a specific point in time.
 * Contains data from multiple modalities (CPU, power, temperature, etc.).
 */
public class TelemetrySnapshot {
    private final double timestamp;
    private final Map<String, ComponentTelemetry> componentData;
    private final Map<TelemetryType, Object> aggregatedMetrics;

    public TelemetrySnapshot(double timestamp) {
        this.timestamp = timestamp;
        this.componentData = new HashMap<>();
        this.aggregatedMetrics = new HashMap<>();
    }

    /**
     * Add telemetry data for a specific component (host or VM).
     */
    public void addComponentData(String componentId, ComponentTelemetry data) {
        componentData.put(componentId, data);
    }

    /**
     * Add aggregated metrics for a specific telemetry type.
     */
    public void addAggregatedMetric(TelemetryType type, Object value) {
        aggregatedMetrics.put(type, value);
    }

    public double getTimestamp() {
        return timestamp;
    }

    public Map<String, ComponentTelemetry> getComponentData() {
        return componentData;
    }

    public Map<TelemetryType, Object> getAggregatedMetrics() {
        return aggregatedMetrics;
    }

    /**
     * Represents telemetry data for a single component.
     */
    public static class ComponentTelemetry {
        private final String componentId;
        private final String componentType; // "HOST" or "VM"
        private final Map<String, Double> metrics;
        private final Map<String, String> metadata;

        public ComponentTelemetry(String componentId, String componentType) {
            this.componentId = componentId;
            this.componentType = componentType;
            this.metrics = new HashMap<>();
            this.metadata = new HashMap<>();
        }

        public void addMetric(String name, double value) {
            metrics.put(name, value);
        }

        public void addMetadata(String key, String value) {
            metadata.put(key, value);
        }

        public String getComponentId() { return componentId; }
        public String getComponentType() { return componentType; }
        public Map<String, Double> getMetrics() { return metrics; }
        public Map<String, String> getMetadata() { return metadata; }
    }
}

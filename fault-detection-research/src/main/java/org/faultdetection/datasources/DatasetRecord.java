package org.faultdetection.datasources;

import java.util.HashMap;
import java.util.Map;

/**
 * Generic record from external datasets.
 */
public class DatasetRecord {
    private final double timestamp;
    private final Map<String, Object> fields;
    private final String datasetType;

    public DatasetRecord(String datasetType, double timestamp) {
        this.datasetType = datasetType;
        this.timestamp = timestamp;
        this.fields = new HashMap<>();
    }

    public void addField(String name, Object value) {
        fields.put(name, value);
    }

    public double getTimestamp() {
        return timestamp;
    }

    public Map<String, Object> getFields() {
        return fields;
    }

    public String getDatasetType() {
        return datasetType;
    }

    public Object getField(String name) {
        return fields.get(name);
    }

    public String getFieldAsString(String name) {
        Object value = fields.get(name);
        return value != null ? value.toString() : null;
    }

    public Double getFieldAsDouble(String name) {
        Object value = fields.get(name);
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return null;
    }
}

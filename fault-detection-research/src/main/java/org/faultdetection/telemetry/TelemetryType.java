package org.faultdetection.telemetry;

/**
 * Enumeration of different telemetry data types collected in the system.
 */
public enum TelemetryType {
    /**
     * CPU utilization metrics (percentage, load, etc.)
     */
    CPU_METRICS,

    /**
     * Power consumption data (watts, voltage, current)
     */
    POWER_METRICS,

    /**
     * Temperature readings (Celsius, from various sensors)
     */
    TEMPERATURE_METRICS,

    /**
     * Vibration data (acceleration, frequency)
     */
    VIBRATION_METRICS,

    /**
     * Memory utilization and statistics
     */
    MEMORY_METRICS,

    /**
     * Storage I/O and health metrics
     */
    STORAGE_METRICS,

    /**
     * Network traffic and statistics
     */
    NETWORK_METRICS,

    /**
     * System logs and event data
     */
    SYSTEM_LOGS,

    /**
     * Application-level logs
     */
    APPLICATION_LOGS,

    /**
     * Combined/fused metrics from multiple sources
     */
    FUSED_METRICS
}

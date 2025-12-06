package org.faultdetection.telemetry;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;
import org.faultdetection.telemetry.TelemetrySnapshot.ComponentTelemetry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Writes telemetry data to CSV files in Prometheus-compatible format.
 * Supports multiple output formats and compression.
 */
public class TelemetryWriter implements AutoCloseable {
    private static final Logger logger = LoggerFactory.getLogger(TelemetryWriter.class);

    private final Path outputPath;
    private CSVPrinter csvPrinter;
    private boolean headerWritten = false;

    private static final String[] HEADER = {
        "timestamp",
        "component_id",
        "component_type",
        "cpu_utilization",
        "cpu_allocated_mips",
        "cpu_available_mips",
        "power_consumption_watts",
        "temperature_celsius",
        "temperature_cpu_sensor",
        "temperature_ambient",
        "vibration_magnitude",
        "vibration_frequency_hz",
        "ram_utilization",
        "ram_available_mb",
        "storage_utilization",
        "storage_available_mb",
        "bw_utilization",
        "status",
        "failed",
        "host_id",
        "vms_count",
        "cloudlets_count"
    };

    public TelemetryWriter(Path outputPath) throws IOException {
        this.outputPath = outputPath;
        initializeWriter();
    }

    private void initializeWriter() throws IOException {
        Files.createDirectories(outputPath.getParent());
        BufferedWriter writer = Files.newBufferedWriter(outputPath);
        csvPrinter = new CSVPrinter(writer, CSVFormat.DEFAULT);
        logger.info("Initialized telemetry writer: {}", outputPath);
    }

    /**
     * Write a telemetry snapshot to the CSV file.
     */
    public void write(TelemetrySnapshot snapshot) throws IOException {
        if (!headerWritten) {
            csvPrinter.printRecord((Object[]) HEADER);
            headerWritten = true;
        }

        double timestamp = snapshot.getTimestamp();

        for (Map.Entry<String, ComponentTelemetry> entry : snapshot.getComponentData().entrySet()) {
            ComponentTelemetry telemetry = entry.getValue();
            writeComponentTelemetry(timestamp, telemetry);
        }

        csvPrinter.flush();
    }

    private void writeComponentTelemetry(double timestamp, ComponentTelemetry telemetry) throws IOException {
        List<Object> record = new ArrayList<>();

        Map<String, Double> metrics = telemetry.getMetrics();
        Map<String, String> metadata = telemetry.getMetadata();

        record.add(timestamp);
        record.add(telemetry.getComponentId());
        record.add(telemetry.getComponentType());

        // Add metrics (use 0 or empty if not present)
        record.add(metrics.getOrDefault("cpu_utilization", 0.0));
        record.add(metrics.getOrDefault("cpu_allocated_mips", 0.0));
        record.add(metrics.getOrDefault("cpu_available_mips", 0.0));
        record.add(metrics.getOrDefault("power_consumption_watts", 0.0));
        record.add(metrics.getOrDefault("temperature_celsius", 0.0));
        record.add(metrics.getOrDefault("temperature_cpu_sensor", 0.0));
        record.add(metrics.getOrDefault("temperature_ambient", 0.0));
        record.add(metrics.getOrDefault("vibration_magnitude", 0.0));
        record.add(metrics.getOrDefault("vibration_frequency_hz", 0.0));
        record.add(metrics.getOrDefault("ram_utilization", 0.0));
        record.add(metrics.getOrDefault("ram_available_mb", 0.0));
        record.add(metrics.getOrDefault("storage_utilization", 0.0));
        record.add(metrics.getOrDefault("storage_available_mb", 0.0));
        record.add(metrics.getOrDefault("bw_utilization", 0.0));

        // Add metadata
        record.add(metadata.getOrDefault("status", "UNKNOWN"));
        record.add(metadata.getOrDefault("failed", "false"));
        record.add(metadata.getOrDefault("host_id", ""));
        record.add(metadata.getOrDefault("vms_count", "0"));
        record.add(metadata.getOrDefault("cloudlets_count", "0"));

        csvPrinter.printRecord(record);
    }

    /**
     * Write telemetry data in JSON format (alternative to CSV).
     */
    public void writeJson(TelemetrySnapshot snapshot, Path jsonPath) throws IOException {
        // Implementation for JSON output
        // Could use Gson to serialize the snapshot
        logger.info("JSON output not yet implemented");
    }

    @Override
    public void close() throws IOException {
        if (csvPrinter != null) {
            csvPrinter.flush();
            csvPrinter.close();
            logger.info("Closed telemetry writer");
        }
    }

    public Path getOutputPath() {
        return outputPath;
    }
}

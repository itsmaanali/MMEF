package org.faultdetection.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Configuration class for the fault detection research project.
 * Contains all simulation parameters, model settings, and evaluation criteria.
 */
public class ResearchConfig {
    // Simulation parameters
    private int numberOfHosts = 10;
    private int numberOfVms = 50;
    private int numberOfCloudlets = 200;
    private double simulationDuration = 3600.0; // seconds
    private double telemetryInterval = 1.0; // seconds

    // Fault injection parameters
    private double faultInjectionStart = 1800.0; // Start faults at 30 minutes
    private double faultProbability = 0.15;
    private String[] faultTypes = {"FAN_FAILURE", "POWER_SUPPLY_DEGRADATION", "DISK_FAILURE", "THERMAL_ISSUE"};

    // Data collection parameters
    private boolean collectCpuMetrics = true;
    private boolean collectPowerMetrics = true;
    private boolean collectTemperatureMetrics = true;
    private boolean collectVibrationMetrics = true;
    private boolean collectSystemLogs = true;

    // Multi-Modal Fusion parameters
    private String fusionStrategy = "WEIGHTED_AVERAGE"; // Options: WEIGHTED_AVERAGE, ATTENTION, LATE_FUSION
    private double[] modalityWeights = {0.3, 0.25, 0.25, 0.2}; // CPU, Power, Temp, Vibration

    // ML Model parameters
    private boolean useRandomForest = true;
    private boolean useXGBoost = true;
    private boolean useLSTMAutoencoder = true;
    private boolean useIsolationForest = true;

    // Evaluation parameters
    private double earlyDetectionThresholdSeconds = 300.0; // 5 minutes before failure
    private double confidenceThreshold = 0.7;

    // File paths
    private String outputDirectory = "output/research-results";
    private String telemetryOutputPath = "output/telemetry";
    private String modelsDirectory = "models";
    private String datasetsDirectory = "datasets";

    // Dataset sources configuration
    private DatasetConfig[] datasetSources = {
        new DatasetConfig("Google Cluster Trace", "datasets/google-cluster", true),
        new DatasetConfig("Alibaba Cluster Trace", "datasets/alibaba-cluster", true),
        new DatasetConfig("BGL Logs", "datasets/bgl-logs", true),
        new DatasetConfig("NASA Prognostics", "datasets/nasa-prognostics", true)
    };

    public static ResearchConfig loadDefault() {
        ResearchConfig config = new ResearchConfig();

        // Create necessary directories
        try {
            Files.createDirectories(Paths.get(config.outputDirectory));
            Files.createDirectories(Paths.get(config.telemetryOutputPath));
            Files.createDirectories(Paths.get(config.modelsDirectory));
            Files.createDirectories(Paths.get(config.datasetsDirectory));
        } catch (IOException e) {
            throw new RuntimeException("Failed to create output directories", e);
        }

        return config;
    }

    public static ResearchConfig loadFromFile(Path configPath) throws IOException {
        Gson gson = new Gson();
        String json = Files.readString(configPath);
        return gson.fromJson(json, ResearchConfig.class);
    }

    public void saveToFile(Path configPath) throws IOException {
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        String json = gson.toJson(this);
        Files.writeString(configPath, json);
    }

    // Getters
    public int getNumberOfHosts() { return numberOfHosts; }
    public int getNumberOfVms() { return numberOfVms; }
    public int getNumberOfCloudlets() { return numberOfCloudlets; }
    public double getSimulationDuration() { return simulationDuration; }
    public double getTelemetryInterval() { return telemetryInterval; }
    public double getFaultInjectionStart() { return faultInjectionStart; }
    public double getFaultProbability() { return faultProbability; }
    public String[] getFaultTypes() { return faultTypes; }
    public boolean isCollectCpuMetrics() { return collectCpuMetrics; }
    public boolean isCollectPowerMetrics() { return collectPowerMetrics; }
    public boolean isCollectTemperatureMetrics() { return collectTemperatureMetrics; }
    public boolean isCollectVibrationMetrics() { return collectVibrationMetrics; }
    public boolean isCollectSystemLogs() { return collectSystemLogs; }
    public String getFusionStrategy() { return fusionStrategy; }
    public double[] getModalityWeights() { return modalityWeights; }
    public boolean isUseRandomForest() { return useRandomForest; }
    public boolean isUseXGBoost() { return useXGBoost; }
    public boolean isUseLSTMAutoencoder() { return useLSTMAutoencoder; }
    public boolean isUseIsolationForest() { return useIsolationForest; }
    public double getEarlyDetectionThresholdSeconds() { return earlyDetectionThresholdSeconds; }
    public double getConfidenceThreshold() { return confidenceThreshold; }
    public String getOutputDirectory() { return outputDirectory; }
    public String getTelemetryOutputPath() { return telemetryOutputPath; }
    public String getModelsDirectory() { return modelsDirectory; }
    public String getDatasetsDirectory() { return datasetsDirectory; }
    public DatasetConfig[] getDatasetSources() { return datasetSources; }

    // Setters (for customization)
    public void setNumberOfHosts(int numberOfHosts) { this.numberOfHosts = numberOfHosts; }
    public void setNumberOfVms(int numberOfVms) { this.numberOfVms = numberOfVms; }
    public void setSimulationDuration(double simulationDuration) { this.simulationDuration = simulationDuration; }

    public static class DatasetConfig {
        private String name;
        private String path;
        private boolean enabled;

        public DatasetConfig(String name, String path, boolean enabled) {
            this.name = name;
            this.path = path;
            this.enabled = enabled;
        }

        public String getName() { return name; }
        public String getPath() { return path; }
        public boolean isEnabled() { return enabled; }
    }
}

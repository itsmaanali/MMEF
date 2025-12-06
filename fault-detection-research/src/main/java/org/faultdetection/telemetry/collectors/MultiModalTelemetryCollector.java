package org.faultdetection.telemetry.collectors;

import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.vms.Vm;
import org.faultdetection.telemetry.TelemetryCollector;
import org.faultdetection.telemetry.TelemetrySnapshot;
import org.faultdetection.telemetry.TelemetrySnapshot.ComponentTelemetry;
import org.faultdetection.telemetry.TelemetryType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Random;

/**
 * Multi-modal telemetry collector that gathers CPU, power, temperature,
 * and vibration data from datacenter components.
 *
 * This collector simulates realistic sensor data with noise and correlations.
 */
public class MultiModalTelemetryCollector implements TelemetryCollector {
    private static final Logger logger = LoggerFactory.getLogger(MultiModalTelemetryCollector.class);

    private final Random random;
    private boolean initialized = false;

    // Simulation parameters
    private static final double BASE_TEMPERATURE = 35.0; // Celsius
    private static final double TEMP_PER_CPU_PERCENT = 30.0;
    private static final double TEMP_NOISE_STDDEV = 2.0;

    private static final double BASE_VIBRATION = 0.5; // arbitrary units
    private static final double VIBRATION_PER_CPU = 0.3;
    private static final double VIBRATION_NOISE_STDDEV = 0.1;

    public MultiModalTelemetryCollector() {
        this.random = new Random(42);
    }

    public MultiModalTelemetryCollector(long seed) {
        this.random = new Random(seed);
    }

    @Override
    public void initialize() {
        logger.info("Initializing Multi-Modal Telemetry Collector");
        initialized = true;
    }

    @Override
    public TelemetrySnapshot collect(double timestamp, List<Host> hosts, List<Vm> vms) {
        if (!initialized) {
            throw new IllegalStateException("Collector must be initialized before use");
        }

        TelemetrySnapshot snapshot = new TelemetrySnapshot(timestamp);

        // Collect host-level telemetry
        for (Host host : hosts) {
            ComponentTelemetry hostTelemetry = collectHostTelemetry(host);
            snapshot.addComponentData("host-" + host.getId(), hostTelemetry);
        }

        // Collect VM-level telemetry
        for (Vm vm : vms) {
            if (vm.getHost() != null && vm.getHost() != Host.NULL) {
                ComponentTelemetry vmTelemetry = collectVmTelemetry(vm);
                snapshot.addComponentData("vm-" + vm.getId(), vmTelemetry);
            }
        }

        return snapshot;
    }

    private ComponentTelemetry collectHostTelemetry(Host host) {
        ComponentTelemetry telemetry = new ComponentTelemetry(
            String.valueOf(host.getId()),
            "HOST"
        );

        // CPU Metrics
        double cpuUtilization = host.getCpuPercentUtilization();
        telemetry.addMetric("cpu_utilization", cpuUtilization);
        telemetry.addMetric("cpu_allocated_mips", host.getTotalAllocatedMips());
        telemetry.addMetric("cpu_available_mips", host.getCpuMipsAvailability());

        // Power Metrics
        double powerConsumption = host.getPowerModel().getPower(cpuUtilization);
        telemetry.addMetric("power_consumption_watts", powerConsumption);
        telemetry.addMetric("power_max_watts", host.getPowerModel().getMaxPower());

        // Temperature Metrics (simulated based on CPU usage)
        double temperature = calculateTemperature(cpuUtilization);
        telemetry.addMetric("temperature_celsius", temperature);
        telemetry.addMetric("temperature_cpu_sensor", temperature + random.nextGaussian() * 1.0);
        telemetry.addMetric("temperature_ambient", BASE_TEMPERATURE + random.nextGaussian() * 0.5);

        // Vibration Metrics (simulated based on CPU and fan activity)
        double vibration = calculateVibration(cpuUtilization);
        telemetry.addMetric("vibration_magnitude", vibration);
        telemetry.addMetric("vibration_frequency_hz", 50 + cpuUtilization * 30);

        // Memory Metrics
        telemetry.addMetric("ram_utilization", host.getRamUtilization());
        telemetry.addMetric("ram_available_mb", host.getRam().getAvailableResource());

        // Storage Metrics
        telemetry.addMetric("storage_available_mb", host.getStorage().getAvailableResource());
        telemetry.addMetric("storage_utilization", host.getStorageUtilization());

        // Metadata
        telemetry.addMetadata("status", host.isActive() ? "ACTIVE" : "INACTIVE");
        telemetry.addMetadata("failed", host.isFailed() ? "true" : "false");
        telemetry.addMetadata("vms_count", String.valueOf(host.getVmList().size()));

        return telemetry;
    }

    private ComponentTelemetry collectVmTelemetry(Vm vm) {
        ComponentTelemetry telemetry = new ComponentTelemetry(
            String.valueOf(vm.getId()),
            "VM"
        );

        Host host = vm.getHost();

        // CPU Metrics
        double vmCpuUtilization = vm.getCpuPercentUtilization();
        telemetry.addMetric("cpu_utilization", vmCpuUtilization);
        telemetry.addMetric("cpu_total_mips", vm.getTotalMipsCapacity());
        telemetry.addMetric("cpu_requested_mips", vm.getCurrentRequestedTotalMips());

        // Memory Metrics
        telemetry.addMetric("ram_utilization", vm.getRamUtilization());
        telemetry.addMetric("ram_allocated_mb", vm.getRam().getAllocatedResource());

        // Storage Metrics
        telemetry.addMetric("storage_allocated_mb", vm.getStorage().getAllocatedResource());

        // Bandwidth Metrics
        telemetry.addMetric("bw_utilization", vm.getBwUtilization());

        // Metadata
        telemetry.addMetadata("status", vm.isCreated() ? "RUNNING" : "STOPPED");
        telemetry.addMetadata("host_id", String.valueOf(host.getId()));
        telemetry.addMetadata("cloudlets_count", String.valueOf(vm.getCloudletScheduler().getCloudletList().size()));

        return telemetry;
    }

    /**
     * Calculate simulated temperature based on CPU utilization.
     * Temperature increases with CPU load and includes Gaussian noise.
     */
    private double calculateTemperature(double cpuUtilization) {
        double baseTemp = BASE_TEMPERATURE + (cpuUtilization * TEMP_PER_CPU_PERCENT);
        double noise = random.nextGaussian() * TEMP_NOISE_STDDEV;
        return Math.max(BASE_TEMPERATURE, baseTemp + noise);
    }

    /**
     * Calculate simulated vibration based on CPU utilization and fan speed.
     * Higher CPU usage leads to higher fan speeds and more vibration.
     */
    private double calculateVibration(double cpuUtilization) {
        double baseVibration = BASE_VIBRATION + (cpuUtilization * VIBRATION_PER_CPU);
        double noise = random.nextGaussian() * VIBRATION_NOISE_STDDEV;
        return Math.max(0, baseVibration + noise);
    }

    @Override
    public void shutdown() {
        logger.info("Shutting down Multi-Modal Telemetry Collector");
        initialized = false;
    }

    @Override
    public TelemetryType getType() {
        return TelemetryType.FUSED_METRICS;
    }
}

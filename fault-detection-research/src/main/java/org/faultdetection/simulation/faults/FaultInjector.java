package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;
import org.faultdetection.config.ResearchConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Fault injector for simulating hardware failures in datacenter hosts.
 * Supports multiple fault types: fan failures, power supply degradation,
 * disk failures, and thermal issues.
 */
public class FaultInjector {
    private static final Logger logger = LoggerFactory.getLogger(FaultInjector.class);

    private final ResearchConfig config;
    private final List<Host> hosts;
    private final Random random;
    private final Map<Long, List<HardwareFault>> activeFaults;
    private final Map<Long, FaultHistory> faultHistory;

    public FaultInjector(ResearchConfig config, List<Host> hosts) {
        this.config = config;
        this.hosts = hosts;
        this.random = new Random(System.currentTimeMillis());
        this.activeFaults = new HashMap<>();
        this.faultHistory = new HashMap<>();
    }

    public void initialize() {
        for (Host host : hosts) {
            activeFaults.put(host.getId(), new ArrayList<>());
            faultHistory.put(host.getId(), new FaultHistory(host.getId()));
        }
        logger.info("Fault injector initialized for {} hosts", hosts.size());
    }

    /**
     * Inject faults based on configured probability and fault types.
     */
    public void injectFaults(double currentTime) {
        for (Host host : hosts) {
            // Check if we should inject a new fault
            if (random.nextDouble() < config.getFaultProbability() * 0.01) {
                HardwareFault fault = generateRandomFault(host, currentTime);
                injectFault(host, fault);
            }

            // Update existing faults
            updateExistingFaults(host, currentTime);
        }
    }

    private HardwareFault generateRandomFault(Host host, double timestamp) {
        String[] faultTypes = config.getFaultTypes();
        String faultType = faultTypes[random.nextInt(faultTypes.length)];

        return switch (faultType) {
            case "FAN_FAILURE" -> new FanFailureFault(timestamp, host.getId());
            case "POWER_SUPPLY_DEGRADATION" -> new PowerSupplyFault(timestamp, host.getId());
            case "DISK_FAILURE" -> new DiskFailureFault(timestamp, host.getId());
            case "THERMAL_ISSUE" -> new ThermalFault(timestamp, host.getId());
            default -> new GenericFault(timestamp, host.getId(), faultType);
        };
    }

    private void injectFault(Host host, HardwareFault fault) {
        activeFaults.get(host.getId()).add(fault);
        faultHistory.get(host.getId()).recordFault(fault);

        logger.info("Injected {} on host {} at time {}",
            fault.getFaultType(), host.getId(), fault.getStartTime());

        // Apply fault effects to host
        fault.applyToHost(host);
    }

    private void updateExistingFaults(Host host, double currentTime) {
        List<HardwareFault> faults = activeFaults.get(host.getId());
        List<HardwareFault> toRemove = new ArrayList<>();

        for (HardwareFault fault : faults) {
            fault.update(currentTime);

            if (fault.isResolved()) {
                toRemove.add(fault);
                logger.info("Fault {} on host {} resolved at time {}",
                    fault.getFaultType(), host.getId(), currentTime);
            }
        }

        faults.removeAll(toRemove);
    }

    /**
     * Get all faults affecting a specific host.
     */
    public List<HardwareFault> getActiveFaults(long hostId) {
        return new ArrayList<>(activeFaults.getOrDefault(hostId, Collections.emptyList()));
    }

    /**
     * Get fault history for analysis and ground truth labeling.
     */
    public FaultHistory getFaultHistory(long hostId) {
        return faultHistory.get(hostId);
    }

    /**
     * Get all fault history records (for creating ground truth labels).
     */
    public Map<Long, FaultHistory> getAllFaultHistory() {
        return new HashMap<>(faultHistory);
    }

    /**
     * Check if a host has any active faults at a given time.
     */
    public boolean hasActiveFaults(long hostId, double timestamp) {
        List<HardwareFault> faults = activeFaults.get(hostId);
        if (faults == null) return false;

        return faults.stream().anyMatch(f ->
            f.getStartTime() <= timestamp &&
            (f.getEndTime() == null || f.getEndTime() > timestamp)
        );
    }

    /**
     * Get the severity of faults on a host (0.0 = no faults, 1.0 = critical).
     */
    public double getFaultSeverity(long hostId) {
        List<HardwareFault> faults = activeFaults.get(hostId);
        if (faults == null || faults.isEmpty()) return 0.0;

        return faults.stream()
            .mapToDouble(HardwareFault::getSeverity)
            .max()
            .orElse(0.0);
    }
}

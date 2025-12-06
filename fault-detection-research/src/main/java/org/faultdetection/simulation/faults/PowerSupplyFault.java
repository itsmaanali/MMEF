package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;

/**
 * Simulates power supply degradation, causing power fluctuations
 * and efficiency loss.
 */
public class PowerSupplyFault extends HardwareFault {
    private static final double BASE_DURATION = 600.0; // 10 minutes
    private double powerEfficiencyLoss = 0.15; // 15% efficiency loss

    public PowerSupplyFault(double startTime, long hostId) {
        super(startTime, hostId);
        this.severity = 0.6;
    }

    @Override
    public void applyToHost(Host host) {
        // Power supply degradation increases power consumption
        // This would be reflected in power telemetry
    }

    @Override
    public void update(double currentTime) {
        double elapsed = currentTime - startTime;

        if (elapsed >= BASE_DURATION && !resolved) {
            resolve(currentTime);
        }

        // Gradually worsening
        if (!resolved) {
            severity = Math.min(0.9, 0.6 + (elapsed / BASE_DURATION) * 0.3);
        }
    }

    @Override
    public String getFaultType() {
        return "POWER_SUPPLY_DEGRADATION";
    }

    @Override
    public String getAffectedComponent() {
        return "POWER_SUPPLY";
    }

    public double getPowerIncreaseFactor() {
        return 1.0 + (powerEfficiencyLoss * severity);
    }
}

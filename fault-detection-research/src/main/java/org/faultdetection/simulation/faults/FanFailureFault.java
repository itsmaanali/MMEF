package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;

/**
 * Simulates a fan failure fault, which leads to increased temperature
 * and vibration changes.
 */
public class FanFailureFault extends HardwareFault {
    private static final double BASE_DURATION = 300.0; // 5 minutes
    private double temperatureIncrease = 15.0; // Celsius

    public FanFailureFault(double startTime, long hostId) {
        super(startTime, hostId);
        this.severity = 0.7; // High severity
    }

    @Override
    public void applyToHost(Host host) {
        // Fan failure causes temperature to rise
        // In a real implementation, this would modify host temperature sensors
        // For simulation, this is tracked by the fault injector
    }

    @Override
    public void update(double currentTime) {
        double elapsed = currentTime - startTime;

        // Fault resolves after base duration
        if (elapsed >= BASE_DURATION && !resolved) {
            resolve(currentTime);
        }

        // Severity increases over time
        if (!resolved) {
            severity = Math.min(1.0, 0.7 + (elapsed / BASE_DURATION) * 0.3);
        }
    }

    @Override
    public String getFaultType() {
        return "FAN_FAILURE";
    }

    @Override
    public String getAffectedComponent() {
        return "COOLING_FAN";
    }

    public double getTemperatureIncrease() {
        return temperatureIncrease * severity;
    }
}

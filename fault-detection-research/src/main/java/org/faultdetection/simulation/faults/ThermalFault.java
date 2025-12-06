package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;

/**
 * Simulates thermal issues (overheating) due to cooling system problems
 * or environmental factors.
 */
public class ThermalFault extends HardwareFault {
    private static final double BASE_DURATION = 400.0; // ~6.7 minutes
    private double temperatureIncrease = 20.0; // Celsius

    public ThermalFault(double startTime, long hostId) {
        super(startTime, hostId);
        this.severity = 0.75;
    }

    @Override
    public void applyToHost(Host host) {
        // Thermal issues cause temperature spikes
    }

    @Override
    public void update(double currentTime) {
        double elapsed = currentTime - startTime;

        if (elapsed >= BASE_DURATION && !resolved) {
            resolve(currentTime);
        }

        // Temperature increases non-linearly
        if (!resolved) {
            double progress = elapsed / BASE_DURATION;
            severity = Math.min(1.0, 0.75 + progress * 0.25);
        }
    }

    @Override
    public String getFaultType() {
        return "THERMAL_ISSUE";
    }

    @Override
    public String getAffectedComponent() {
        return "THERMAL_MANAGEMENT";
    }

    public double getTemperatureIncrease() {
        return temperatureIncrease * severity;
    }
}

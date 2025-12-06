package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;

/**
 * Generic fault implementation for custom fault types.
 */
public class GenericFault extends HardwareFault {
    private final String faultType;
    private static final double BASE_DURATION = 300.0;

    public GenericFault(double startTime, long hostId, String faultType) {
        super(startTime, hostId);
        this.faultType = faultType;
        this.severity = 0.5;
    }

    @Override
    public void applyToHost(Host host) {
        // Generic implementation
    }

    @Override
    public void update(double currentTime) {
        double elapsed = currentTime - startTime;
        if (elapsed >= BASE_DURATION && !resolved) {
            resolve(currentTime);
        }
    }

    @Override
    public String getFaultType() {
        return faultType;
    }

    @Override
    public String getAffectedComponent() {
        return "GENERIC";
    }
}

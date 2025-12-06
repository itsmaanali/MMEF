package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;

/**
 * Abstract base class for hardware faults that can be injected into hosts.
 */
public abstract class HardwareFault {
    protected final double startTime;
    protected final long hostId;
    protected Double endTime;
    protected double severity; // 0.0 to 1.0
    protected boolean resolved;

    public HardwareFault(double startTime, long hostId) {
        this.startTime = startTime;
        this.hostId = hostId;
        this.endTime = null;
        this.resolved = false;
        this.severity = 0.5; // Default severity
    }

    /**
     * Apply the fault effects to a host.
     */
    public abstract void applyToHost(Host host);

    /**
     * Update the fault state based on current time.
     */
    public abstract void update(double currentTime);

    /**
     * Get the type/name of this fault.
     */
    public abstract String getFaultType();

    /**
     * Get the component affected by this fault.
     */
    public abstract String getAffectedComponent();

    public double getStartTime() {
        return startTime;
    }

    public Double getEndTime() {
        return endTime;
    }

    public long getHostId() {
        return hostId;
    }

    public double getSeverity() {
        return severity;
    }

    public void setSeverity(double severity) {
        this.severity = Math.max(0.0, Math.min(1.0, severity));
    }

    public boolean isResolved() {
        return resolved;
    }

    public void resolve(double currentTime) {
        this.resolved = true;
        this.endTime = currentTime;
    }
}

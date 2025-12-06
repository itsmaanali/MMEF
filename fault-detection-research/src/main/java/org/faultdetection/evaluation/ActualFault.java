package org.faultdetection.evaluation;

/**
 * Represents an actual fault from ground truth (fault injection logs).
 */
public class ActualFault {
    private final double timestamp;
    private final String faultType;
    private final String component;
    private final long hostId;

    public ActualFault(double timestamp, String faultType, String component, long hostId) {
        this.timestamp = timestamp;
        this.faultType = faultType;
        this.component = component;
        this.hostId = hostId;
    }

    public double getTimestamp() {
        return timestamp;
    }

    public String getFaultType() {
        return faultType;
    }

    public String getComponent() {
        return component;
    }

    public long getHostId() {
        return hostId;
    }

    @Override
    public String toString() {
        return String.format("ActualFault{time=%.1f, type=%s, component=%s, host=%d}",
            timestamp, faultType, component, hostId);
    }
}

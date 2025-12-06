package org.faultdetection.simulation.faults;

import org.cloudsimplus.hosts.Host;

/**
 * Simulates disk failure, causing I/O errors and storage degradation.
 */
public class DiskFailureFault extends HardwareFault {
    private static final double BASE_DURATION = 450.0; // 7.5 minutes

    public DiskFailureFault(double startTime, long hostId) {
        super(startTime, hostId);
        this.severity = 0.8; // High severity - data at risk
    }

    @Override
    public void applyToHost(Host host) {
        // Disk failure would show up in I/O metrics and system logs
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
        return "DISK_FAILURE";
    }

    @Override
    public String getAffectedComponent() {
        return "STORAGE_DISK";
    }
}

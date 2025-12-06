package org.faultdetection.simulation.faults;

import java.util.ArrayList;
import java.util.List;

/**
 * Tracks the history of faults for a specific host.
 * Used for creating ground truth labels for ML training.
 */
public class FaultHistory {
    private final long hostId;
    private final List<FaultRecord> records;

    public FaultHistory(long hostId) {
        this.hostId = hostId;
        this.records = new ArrayList<>();
    }

    public void recordFault(HardwareFault fault) {
        records.add(new FaultRecord(fault));
    }

    public List<FaultRecord> getRecords() {
        return new ArrayList<>(records);
    }

    public long getHostId() {
        return hostId;
    }

    /**
     * Check if there was a fault active at a specific time.
     */
    public boolean hasFaultAt(double timestamp) {
        return records.stream().anyMatch(r ->
            r.startTime <= timestamp &&
            (r.endTime == null || r.endTime > timestamp)
        );
    }

    /**
     * Get faults active at a specific time.
     */
    public List<FaultRecord> getFaultsAt(double timestamp) {
        return records.stream()
            .filter(r -> r.startTime <= timestamp &&
                        (r.endTime == null || r.endTime > timestamp))
            .toList();
    }

    public static class FaultRecord {
        private final String faultType;
        private final String component;
        private final double startTime;
        private final Double endTime;
        private final double severity;

        public FaultRecord(HardwareFault fault) {
            this.faultType = fault.getFaultType();
            this.component = fault.getAffectedComponent();
            this.startTime = fault.getStartTime();
            this.endTime = fault.getEndTime();
            this.severity = fault.getSeverity();
        }

        public String getFaultType() { return faultType; }
        public String getComponent() { return component; }
        public double getStartTime() { return startTime; }
        public Double getEndTime() { return endTime; }
        public double getSeverity() { return severity; }
    }
}

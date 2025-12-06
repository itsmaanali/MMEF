package org.faultdetection.telemetry;

import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.vms.Vm;

import java.util.List;

/**
 * Interface for collecting telemetry data from simulated datacenter components.
 * Supports multiple data modalities including metrics and logs.
 */
public interface TelemetryCollector {

    /**
     * Collect telemetry data at a specific simulation timestamp.
     *
     * @param timestamp Current simulation time in seconds
     * @param hosts List of hosts to collect data from
     * @param vms List of VMs to collect data from
     * @return TelemetrySnapshot containing all collected data
     */
    TelemetrySnapshot collect(double timestamp, List<Host> hosts, List<Vm> vms);

    /**
     * Initialize the collector with necessary parameters.
     */
    void initialize();

    /**
     * Shutdown and cleanup resources.
     */
    void shutdown();

    /**
     * Get the type of telemetry this collector handles.
     */
    TelemetryType getType();
}

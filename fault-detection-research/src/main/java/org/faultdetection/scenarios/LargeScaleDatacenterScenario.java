package org.faultdetection.scenarios;

import org.faultdetection.config.ResearchConfig;
import org.faultdetection.simulation.DatacenterSimulation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Large-scale datacenter scenario simulating realistic production environment.
 * Tests scalability and performance of the fault detection system.
 */
public class LargeScaleDatacenterScenario {
    private static final Logger logger = LoggerFactory.getLogger(LargeScaleDatacenterScenario.class);

    public static void main(String[] args) throws Exception {
        logger.info("Running Large-Scale Datacenter Scenario");

        ResearchConfig config = ResearchConfig.loadDefault();

        // Large datacenter configuration
        config.setNumberOfHosts(100);           // 100 physical servers
        config.setNumberOfVms(500);            // 500 VMs (5:1 ratio)
        config.setSimulationDuration(7200.0);  // 2 hours

        // Increase fault probability for testing
        // config.setFaultProbability(0.25);

        logger.info("Configuration:");
        logger.info("  - Hosts: {}", config.getNumberOfHosts());
        logger.info("  - VMs: {}", config.getNumberOfVms());
        logger.info("  - Duration: {} seconds", config.getSimulationDuration());

        DatacenterSimulation simulation = new DatacenterSimulation(config);
        var telemetryPath = simulation.run();

        logger.info("Large-scale simulation completed!");
        logger.info("Next steps:");
        logger.info("  1. Train ML models: cd python && python training/train_all_models.py --data {}", telemetryPath);
        logger.info("  2. Run fault detection analysis");
        logger.info("  3. Generate research report");
    }
}

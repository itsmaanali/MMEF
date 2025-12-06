package org.faultdetection.scenarios;

import org.faultdetection.config.ResearchConfig;
import org.faultdetection.simulation.DatacenterSimulation;
import org.faultdetection.detection.FaultDetectionEngine;
import org.faultdetection.evaluation.MetricsEvaluator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;

/**
 * Basic fault detection scenario with default configuration.
 * Good starting point for testing the system.
 */
public class BasicFaultDetectionScenario {
    private static final Logger logger = LoggerFactory.getLogger(BasicFaultDetectionScenario.class);

    public static void main(String[] args) throws Exception {
        logger.info("Running Basic Fault Detection Scenario");

        // Create simple configuration
        ResearchConfig config = ResearchConfig.loadDefault();
        config.setNumberOfHosts(5);
        config.setNumberOfVms(20);
        config.setSimulationDuration(600.0); // 10 minutes

        // Run simulation
        logger.info("Step 1: Running CloudSim simulation...");
        DatacenterSimulation simulation = new DatacenterSimulation(config);
        Path telemetryPath = simulation.run();
        logger.info("Telemetry data generated at: {}", telemetryPath);

        // Detect faults
        logger.info("Step 2: Running fault detection...");
        FaultDetectionEngine engine = new FaultDetectionEngine(config);
        engine.loadModels();
        var detectedFaults = engine.detectFaults(telemetryPath);

        // Evaluate
        logger.info("Step 3: Evaluating results...");
        MetricsEvaluator evaluator = new MetricsEvaluator(config);
        var metrics = evaluator.evaluate(detectedFaults, telemetryPath);
        metrics.printReport();

        logger.info("Scenario completed successfully!");
    }
}

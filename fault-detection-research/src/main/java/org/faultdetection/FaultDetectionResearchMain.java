package org.faultdetection;

import org.faultdetection.config.ResearchConfig;
import org.faultdetection.simulation.DatacenterSimulation;
import org.faultdetection.detection.FaultDetectionEngine;
import org.faultdetection.evaluation.MetricsEvaluator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Main entry point for the AI/ML Fault Detection Research Project.
 *
 * This research project implements and evaluates an AI/ML-driven fault detection
 * system using Multi-Modal Event Fusion (MMEF) combined with telemetry data.
 */
public class FaultDetectionResearchMain {
    private static final Logger logger = LoggerFactory.getLogger(FaultDetectionResearchMain.class);

    public static void main(String[] args) {
        logger.info("=".repeat(80));
        logger.info("AI/ML FAULT DETECTION RESEARCH PROJECT");
        logger.info("Multi-Modal Event Fusion for Predictive Hardware Fault Detection");
        logger.info("=".repeat(80));

        try {
            // Load configuration
            ResearchConfig config = ResearchConfig.loadDefault();
            logger.info("Configuration loaded successfully");

            // Phase 1: Run CloudSim simulation to generate telemetry data
            logger.info("\n[PHASE 1] Running CloudSim Datacenter Simulation...");
            DatacenterSimulation simulation = new DatacenterSimulation(config);
            Path telemetryDataPath = simulation.run();
            logger.info("Telemetry data generated at: {}", telemetryDataPath);

            // Phase 2: Process and normalize data
            logger.info("\n[PHASE 2] Processing and normalizing telemetry data...");
            // This will be implemented in the data processing module

            // Phase 3: Multi-Modal Event Fusion
            logger.info("\n[PHASE 3] Applying Multi-Modal Event Fusion...");
            // This will be implemented in the fusion module

            // Phase 4: ML Model Training/Inference
            logger.info("\n[PHASE 4] Running ML models for fault detection...");
            FaultDetectionEngine engine = new FaultDetectionEngine(config);
            engine.loadModels();
            var detectionResults = engine.detectFaults(telemetryDataPath);
            logger.info("Fault detection completed. Detected {} potential faults",
                       detectionResults.size());

            // Phase 5: Evaluation
            logger.info("\n[PHASE 5] Evaluating model performance...");
            MetricsEvaluator evaluator = new MetricsEvaluator(config);
            var metrics = evaluator.evaluate(detectionResults, telemetryDataPath);
            metrics.printReport();

            logger.info("\n" + "=".repeat(80));
            logger.info("Research experiment completed successfully!");
            logger.info("Results saved to: {}", config.getOutputDirectory());
            logger.info("=".repeat(80));

        } catch (Exception e) {
            logger.error("Error during research experiment execution", e);
            System.exit(1);
        }
    }
}

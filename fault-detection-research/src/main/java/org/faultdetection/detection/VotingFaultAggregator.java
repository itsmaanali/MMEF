package org.faultdetection.detection;

import org.faultdetection.ml.PredictionResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

/**
 * Voting-based aggregator that combines predictions from multiple models.
 * Uses majority voting with confidence weighting.
 */
public class VotingFaultAggregator implements FaultAggregator {
    private static final Logger logger = LoggerFactory.getLogger(VotingFaultAggregator.class);

    private static final double MIN_CONFIDENCE_THRESHOLD = 0.5;

    @Override
    public DetectedFault aggregate(Map<String, PredictionResult> modelPredictions, double timestamp) {
        if (modelPredictions.isEmpty()) {
            return DetectedFault.builder()
                .timestamp(timestamp)
                .faultType("NO_MODELS")
                .confidence(0.0)
                .build();
        }

        // Count votes
        int faultVotes = 0;
        int totalVotes = 0;
        double totalConfidence = 0.0;
        Map<String, Integer> faultTypeVotes = new HashMap<>();
        Map<String, Integer> componentVotes = new HashMap<>();

        DetectedFault.Builder builder = DetectedFault.builder().timestamp(timestamp);

        for (Map.Entry<String, PredictionResult> entry : modelPredictions.entrySet()) {
            String modelName = entry.getKey();
            PredictionResult prediction = entry.getValue();

            totalVotes++;
            builder.modelVote(modelName, prediction.getConfidence());

            if (prediction.isFault()) {
                faultVotes++;
                totalConfidence += prediction.getConfidence();

                // Vote for fault type
                String faultType = prediction.getPredictedFaultType();
                faultTypeVotes.put(faultType, faultTypeVotes.getOrDefault(faultType, 0) + 1);

                // Vote for component
                String component = prediction.getAffectedComponent();
                componentVotes.put(component, componentVotes.getOrDefault(component, 0) + 1);
            }
        }

        // Determine if majority agrees there's a fault
        boolean isFault = (double) faultVotes / totalVotes > 0.5;
        double avgConfidence = totalVotes > 0 ? totalConfidence / totalVotes : 0.0;

        if (isFault && avgConfidence >= MIN_CONFIDENCE_THRESHOLD) {
            // Find most voted fault type
            String mostVotedFaultType = faultTypeVotes.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse("UNKNOWN");

            // Find most voted component
            String mostVotedComponent = componentVotes.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse("UNKNOWN");

            builder.faultType(mostVotedFaultType)
                   .affectedComponent(mostVotedComponent)
                   .confidence(avgConfidence)
                   .severity(avgConfidence);

            logger.debug("Detected fault: {} on {} (confidence: {:.3f}, votes: {}/{})",
                mostVotedFaultType, mostVotedComponent, avgConfidence, faultVotes, totalVotes);
        } else {
            builder.faultType("NONE")
                   .affectedComponent("NONE")
                   .confidence(avgConfidence)
                   .severity(0.0);
        }

        return builder.build();
    }
}

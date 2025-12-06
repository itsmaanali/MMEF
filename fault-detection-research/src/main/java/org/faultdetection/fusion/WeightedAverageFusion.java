package org.faultdetection.fusion;

import org.faultdetection.processing.ProcessedData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;

/**
 * Weighted average fusion strategy that combines multiple modalities
 * using configurable weights for each data source.
 *
 * This is a simple but effective fusion approach suitable for baseline experiments.
 */
public class WeightedAverageFusion implements MultiModalFusion {
    private static final Logger logger = LoggerFactory.getLogger(WeightedAverageFusion.class);

    private Map<String, Double> modalityWeights;
    private int outputDimension;

    public WeightedAverageFusion() {
        this.modalityWeights = new HashMap<>();
        // Default weights
        modalityWeights.put("cpu", 0.3);
        modalityWeights.put("power", 0.25);
        modalityWeights.put("temperature", 0.25);
        modalityWeights.put("vibration", 0.2);
    }

    @Override
    public void initialize(Map<String, Object> config) {
        if (config.containsKey("weights")) {
            @SuppressWarnings("unchecked")
            Map<String, Double> weights = (Map<String, Double>) config.get("weights");
            this.modalityWeights = weights;
        }

        logger.info("Initialized WeightedAverageFusion with weights: {}", modalityWeights);
    }

    @Override
    public double[] fuse(Map<String, ProcessedData> modalityData) {
        // Calculate the total output dimension
        int totalDim = modalityData.values().stream()
            .mapToInt(data -> data.getFeatures().length)
            .sum();

        double[] fusedFeatures = new double[totalDim];
        int offset = 0;

        // Concatenate all modality features with weights applied
        for (Map.Entry<String, ProcessedData> entry : modalityData.entrySet()) {
            String modality = entry.getKey();
            double[] features = entry.getValue().getFeatures();
            double weight = modalityWeights.getOrDefault(modality, 1.0);

            // Apply weight to each feature
            for (int i = 0; i < features.length; i++) {
                fusedFeatures[offset + i] = features[i] * weight;
            }

            offset += features.length;
        }

        this.outputDimension = totalDim;
        return fusedFeatures;
    }

    @Override
    public int getOutputDimension() {
        return outputDimension;
    }

    @Override
    public String getStrategyName() {
        return "WEIGHTED_AVERAGE";
    }

    /**
     * Set custom weights for specific modalities.
     */
    public void setModalityWeight(String modality, double weight) {
        modalityWeights.put(modality, weight);
    }

    public Map<String, Double> getModalityWeights() {
        return new HashMap<>(modalityWeights);
    }
}

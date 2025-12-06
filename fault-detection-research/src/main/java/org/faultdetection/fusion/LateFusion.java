package org.faultdetection.fusion;

import org.faultdetection.processing.ProcessedData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

/**
 * Late fusion strategy that keeps modalities separate until final prediction.
 * Each modality's features are concatenated without weighting or transformation.
 *
 * This allows ML models to learn optimal combinations of modalities.
 */
public class LateFusion implements MultiModalFusion {
    private static final Logger logger = LoggerFactory.getLogger(LateFusion.class);

    private int outputDimension;

    @Override
    public void initialize(Map<String, Object> config) {
        logger.info("Initialized LateFusion strategy");
    }

    @Override
    public double[] fuse(Map<String, ProcessedData> modalityData) {
        // Simply concatenate all features
        int totalDim = modalityData.values().stream()
            .mapToInt(data -> data.getFeatures().length)
            .sum();

        double[] fusedFeatures = new double[totalDim];
        int offset = 0;

        for (ProcessedData data : modalityData.values()) {
            double[] features = data.getFeatures();
            System.arraycopy(features, 0, fusedFeatures, offset, features.length);
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
        return "LATE_FUSION";
    }
}

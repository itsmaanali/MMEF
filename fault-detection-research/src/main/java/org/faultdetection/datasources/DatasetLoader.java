package org.faultdetection.datasources;

import java.nio.file.Path;
import java.util.List;

/**
 * Interface for loading external datasets (Google Cluster, Alibaba, BGL, NASA).
 */
public interface DatasetLoader {

    /**
     * Load dataset from the specified path.
     *
     * @param datasetPath Path to dataset files
     * @return Loaded dataset records
     */
    List<DatasetRecord> load(Path datasetPath) throws Exception;

    /**
     * Get the dataset type/name.
     */
    String getDatasetType();

    /**
     * Validate that the dataset is in the expected format.
     */
    boolean validate(Path datasetPath);
}

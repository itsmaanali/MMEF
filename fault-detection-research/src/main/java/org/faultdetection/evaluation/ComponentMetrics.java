package org.faultdetection.evaluation;

import java.util.HashMap;
import java.util.Map;

/**
 * Component-specific detection metrics.
 */
public class ComponentMetrics {
    private final Map<String, ComponentScore> componentScores;

    public ComponentMetrics() {
        this.componentScores = new HashMap<>();
    }

    public void addComponentMetric(String component, double precision, double recall) {
        double f1 = 2 * (precision * recall) / (precision + recall + 1e-10);
        componentScores.put(component, new ComponentScore(precision, recall, f1));
    }

    public Map<String, ComponentScore> getComponentScores() {
        return componentScores;
    }

    public void printReport() {
        System.out.println("\nComponent-Specific Metrics:");
        System.out.println("-".repeat(80));
        System.out.printf("%-20s %-15s %-15s %-15s%n", "Component", "Precision", "Recall", "F1-Score");
        System.out.println("-".repeat(80));

        for (Map.Entry<String, ComponentScore> entry : componentScores.entrySet()) {
            ComponentScore score = entry.getValue();
            System.out.printf("%-20s %-15.3f %-15.3f %-15.3f%n",
                entry.getKey(), score.precision, score.recall, score.f1);
        }
        System.out.println("-".repeat(80));
    }

    public static class ComponentScore {
        public final double precision;
        public final double recall;
        public final double f1;

        public ComponentScore(double precision, double recall, double f1) {
            this.precision = precision;
            this.recall = recall;
            this.f1 = f1;
        }
    }
}

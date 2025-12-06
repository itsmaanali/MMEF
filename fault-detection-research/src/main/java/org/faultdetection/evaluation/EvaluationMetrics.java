package org.faultdetection.evaluation;

/**
 * Container for evaluation metrics.
 */
public class EvaluationMetrics {
    private double precision;
    private double recall;
    private double f1Score;
    private double accuracy;
    private double averageEarlyDetectionTime; // seconds
    private double falsePositiveRate;
    private double falseNegativeRate;
    private int truePositives;
    private int falsePositives;
    private int trueNegatives;
    private int falseNegatives;

    public void printReport() {
        System.out.println("\n" + "=".repeat(80));
        System.out.println("FAULT DETECTION EVALUATION RESULTS");
        System.out.println("=".repeat(80));
        System.out.printf("Precision:                    %.3f%n", precision);
        System.out.printf("Recall:                       %.3f%n", recall);
        System.out.printf("F1 Score:                     %.3f%n", f1Score);
        System.out.printf("Accuracy:                     %.3f%n", accuracy);
        System.out.printf("False Positive Rate:          %.3f%n", falsePositiveRate);
        System.out.printf("False Negative Rate:          %.3f%n", falseNegativeRate);
        System.out.printf("Average Early Detection Time: %.1f seconds%n", averageEarlyDetectionTime);
        System.out.println("\nConfusion Matrix:");
        System.out.printf("  True Positives:  %d%n", truePositives);
        System.out.printf("  False Positives: %d%n", falsePositives);
        System.out.printf("  True Negatives:  %d%n", trueNegatives);
        System.out.printf("  False Negatives: %d%n", falseNegatives);
        System.out.println("=".repeat(80));
    }

    // Getters and setters
    public double getPrecision() { return precision; }
    public void setPrecision(double precision) { this.precision = precision; }

    public double getRecall() { return recall; }
    public void setRecall(double recall) { this.recall = recall; }

    public double getF1Score() { return f1Score; }
    public void setF1Score(double f1Score) { this.f1Score = f1Score; }

    public double getAccuracy() { return accuracy; }
    public void setAccuracy(double accuracy) { this.accuracy = accuracy; }

    public double getAverageEarlyDetectionTime() { return averageEarlyDetectionTime; }
    public void setAverageEarlyDetectionTime(double time) { this.averageEarlyDetectionTime = time; }

    public double getFalsePositiveRate() { return falsePositiveRate; }
    public void setFalsePositiveRate(double rate) { this.falsePositiveRate = rate; }

    public double getFalseNegativeRate() { return falseNegativeRate; }
    public void setFalseNegativeRate(double rate) { this.falseNegativeRate = rate; }

    public void setConfusionMatrix(int tp, int fp, int tn, int fn) {
        this.truePositives = tp;
        this.falsePositives = fp;
        this.trueNegatives = tn;
        this.falseNegatives = fn;
    }
}

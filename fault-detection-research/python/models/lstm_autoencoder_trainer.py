"""LSTM Autoencoder for anomaly detection."""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import precision_recall_fscore_support


def train_lstm_autoencoder(X_train, y_train, X_test, y_test, output_path):
    """
    Train an LSTM Autoencoder for anomaly-based fault detection.

    The autoencoder is trained on normal data and detects faults
    by reconstruction error.

    Args:
        X_train: Training features
        y_train: Training labels (used to filter normal samples)
        X_test: Test features
        y_test: Test labels
        output_path: Path to save the trained model

    Returns:
        Path to the saved model
    """
    print("  Initializing LSTM Autoencoder...")

    # Train only on normal samples (unsupervised approach)
    X_train_normal = X_train[y_train == 0]

    # Reshape for LSTM: (samples, timesteps, features)
    # We'll use a sliding window approach
    timesteps = 10
    n_features = X_train.shape[1]

    def create_sequences(X, timesteps):
        """Create sequences for LSTM input."""
        sequences = []
        for i in range(len(X) - timesteps + 1):
            sequences.append(X[i:i+timesteps])
        return np.array(sequences)

    X_train_seq = create_sequences(X_train_normal, timesteps)
    X_test_seq = create_sequences(X_test, timesteps)

    print(f"  Sequence shape: {X_train_seq.shape}")

    # Build LSTM Autoencoder
    encoder_inputs = keras.Input(shape=(timesteps, n_features))

    # Encoder
    encoded = layers.LSTM(64, activation='relu', return_sequences=True)(encoder_inputs)
    encoded = layers.LSTM(32, activation='relu', return_sequences=False)(encoded)

    # Decoder
    decoded = layers.RepeatVector(timesteps)(encoded)
    decoded = layers.LSTM(32, activation='relu', return_sequences=True)(decoded)
    decoded = layers.LSTM(64, activation='relu', return_sequences=True)(decoded)
    decoded = layers.TimeDistributed(layers.Dense(n_features))(decoded)

    # Autoencoder model
    autoencoder = keras.Model(encoder_inputs, decoded)
    autoencoder.compile(optimizer='adam', loss='mse')

    print("  Training...")
    history = autoencoder.fit(
        X_train_seq, X_train_seq,
        epochs=50,
        batch_size=32,
        validation_split=0.1,
        verbose=0
    )

    print(f"  Final loss: {history.history['loss'][-1]:.4f}")

    # Evaluate using reconstruction error
    print("  Evaluating...")
    reconstructions = autoencoder.predict(X_test_seq, verbose=0)
    mse = np.mean(np.power(X_test_seq - reconstructions, 2), axis=(1, 2))

    # Create test labels (skip first timesteps-1 samples)
    y_test_seq = y_test[timesteps-1:]

    # Determine threshold (e.g., 95th percentile of training reconstruction error)
    train_reconstructions = autoencoder.predict(X_train_seq, verbose=0)
    train_mse = np.mean(np.power(X_train_seq - train_reconstructions, 2), axis=(1, 2))
    threshold = np.percentile(train_mse, 95)

    # Predict anomalies
    y_pred = (mse > threshold).astype(int)

    # Calculate metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test_seq, y_pred, average='binary', zero_division=0
    )

    print(f"  Precision: {precision:.3f}")
    print(f"  Recall:    {recall:.3f}")
    print(f"  F1-Score:  {f1:.3f}")
    print(f"  Threshold: {threshold:.4f}")

    # Save model
    autoencoder.save(output_path)

    # Also save threshold
    threshold_path = str(output_path).replace('.h5', '_threshold.npy')
    np.save(threshold_path, threshold)

    return output_path

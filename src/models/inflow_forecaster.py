"""
LSTM-based Inflow Forecasting Model
Predicts future wastewater inflow for proactive pump control
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Optional
import pickle
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'simulation'))
from data_loader import HSYDataLoader


class LSTMInflowForecaster(nn.Module):
    """
    LSTM model for inflow forecasting

    Features:
    - Historical inflow values (lags)
    - Time features (hour, day of week, weekend)
    - Rolling statistics (mean, std)

    Outputs:
    - Forecast for next 6h (24 timesteps)
    - Forecast for next 24h (96 timesteps)
    """

    def __init__(
        self,
        input_size: int = 10,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = 24,
        dropout: float = 0.2
    ):
        super(LSTMInflowForecaster, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )

        # Output layer
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor of shape (batch, sequence_length, features)

        Returns:
            Predictions of shape (batch, output_size)
        """
        # LSTM forward
        lstm_out, _ = self.lstm(x)

        # Take last timestep output
        last_output = lstm_out[:, -1, :]

        # Generate predictions
        predictions = self.fc(last_output)

        return predictions


class InflowForecastingSystem:
    """
    Complete system for inflow forecasting including:
    - Feature engineering
    - Model training
    - Prediction generation
    - Storm detection
    """

    def __init__(
        self,
        lookback_steps: int = 48,  # 12 hours of history
        forecast_horizon: int = 24,  # 6 hours ahead
        model_path: Optional[str] = None
    ):
        self.lookback_steps = lookback_steps
        self.forecast_horizon = forecast_horizon

        # Model
        self.model = None
        self.scaler = StandardScaler()
        self.feature_scaler = StandardScaler()

        # Load model if path provided
        if model_path and Path(model_path).exists():
            self.load_model(model_path)

    def create_features(self, data: pd.DataFrame, index: int) -> np.ndarray:
        """
        Create features for prediction at given index

        Features:
        - Last N inflow values (lags)
        - Hour of day (cyclical encoding)
        - Day of week (cyclical encoding)
        - Weekend flag
        - Rolling mean (3h, 6h, 12h)
        - Rolling std (6h)

        Args:
            data: DataFrame with inflow data
            index: Current index in data

        Returns:
            Feature array
        """
        features = []

        # Ensure we have enough history
        if index < self.lookback_steps:
            # Pad with first available value
            pad_length = self.lookback_steps - index
            inflow_history = np.concatenate([
                np.full(pad_length, data['F1'].iloc[0]),
                data['F1'].iloc[:index + 1].values
            ])
        else:
            inflow_history = data['F1'].iloc[index - self.lookback_steps + 1:index + 1].values

        # Time features from timestamp
        timestamp = data['Time stamp'].iloc[index]
        hour = timestamp.hour
        day_of_week = timestamp.dayofweek
        is_weekend = 1 if day_of_week >= 5 else 0

        # Cyclical encoding for hour (0-23)
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)

        # Cyclical encoding for day of week (0-6)
        dow_sin = np.sin(2 * np.pi * day_of_week / 7)
        dow_cos = np.cos(2 * np.pi * day_of_week / 7)

        # Rolling statistics (use available data)
        recent_data = data['F1'].iloc[max(0, index - 48):index + 1]
        rolling_mean_3h = recent_data.iloc[-12:].mean() if len(recent_data) >= 12 else recent_data.mean()
        rolling_mean_6h = recent_data.iloc[-24:].mean() if len(recent_data) >= 24 else recent_data.mean()
        rolling_mean_12h = recent_data.mean()
        rolling_std_6h = recent_data.iloc[-24:].std() if len(recent_data) >= 24 else recent_data.std()

        # Current inflow
        current_inflow = data['F1'].iloc[index]

        # Combine all features
        time_features = np.array([
            hour_sin, hour_cos,
            dow_sin, dow_cos,
            is_weekend,
            rolling_mean_3h, rolling_mean_6h, rolling_mean_12h,
            rolling_std_6h,
            current_inflow
        ])

        return time_features

    def prepare_dataset(
        self,
        data: pd.DataFrame,
        train_split: float = 0.8
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training and validation datasets

        Args:
            data: DataFrame with inflow data
            train_split: Fraction of data for training

        Returns:
            X_train, y_train, X_val, y_val
        """
        X = []
        y = []

        # Create sequences
        for i in range(len(data) - self.forecast_horizon):
            if i >= self.lookback_steps:
                # Features
                features = self.create_features(data, i)
                X.append(features)

                # Target: next forecast_horizon inflow values
                targets = data['F1'].iloc[i + 1:i + 1 + self.forecast_horizon].values
                y.append(targets)

        X = np.array(X)
        y = np.array(y)

        # Split into train/val
        split_idx = int(len(X) * train_split)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Fit scalers on training data
        self.feature_scaler.fit(X_train)
        self.scaler.fit(y_train)

        # Scale data
        X_train = self.feature_scaler.transform(X_train)
        X_val = self.feature_scaler.transform(X_val)
        y_train = self.scaler.transform(y_train)
        y_val = self.scaler.transform(y_val)

        return X_train, y_train, X_val, y_val

    def train(
        self,
        data: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ):
        """
        Train the LSTM model

        Args:
            data: DataFrame with historical inflow data
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        """
        print("Preparing dataset...")
        X_train, y_train, X_val, y_val = self.prepare_dataset(data)

        print(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        print(f"Feature size: {X_train.shape[1]}")

        # Create model
        input_size = X_train.shape[1]
        self.model = LSTMInflowForecaster(
            input_size=input_size,
            hidden_size=64,
            num_layers=2,
            output_size=self.forecast_horizon,
            dropout=0.2
        )

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).unsqueeze(1)  # Add sequence dim
        y_train_tensor = torch.FloatTensor(y_train)
        X_val_tensor = torch.FloatTensor(X_val).unsqueeze(1)
        y_val_tensor = torch.FloatTensor(y_val)

        # Training loop
        print("\nTraining LSTM model...")
        best_val_loss = float('inf')

        for epoch in range(epochs):
            self.model.train()

            # Mini-batch training
            total_loss = 0
            num_batches = 0

            for i in range(0, len(X_train_tensor), batch_size):
                batch_X = X_train_tensor[i:i + batch_size]
                batch_y = y_train_tensor[i:i + batch_size]

                # Forward pass
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor)

            avg_train_loss = total_loss / num_batches

            if (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch + 1}/{epochs}], "
                      f"Train Loss: {avg_train_loss:.4f}, "
                      f"Val Loss: {val_loss.item():.4f}")

            # Save best model
            if val_loss.item() < best_val_loss:
                best_val_loss = val_loss.item()

        print(f"\n✓ Training complete! Best validation loss: {best_val_loss:.4f}")

    def predict(
        self,
        data: pd.DataFrame,
        current_index: int,
        horizon_steps: int = 24
    ) -> np.ndarray:
        """
        Generate forecast from current index

        Args:
            data: DataFrame with historical data
            current_index: Current position in data
            horizon_steps: Number of steps to forecast

        Returns:
            Array of forecasted inflow values
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        self.model.eval()

        # Create features
        features = self.create_features(data, current_index)

        # Scale features
        features_scaled = self.feature_scaler.transform(features.reshape(1, -1))

        # Convert to tensor
        X = torch.FloatTensor(features_scaled).unsqueeze(1)

        # Predict
        with torch.no_grad():
            predictions_scaled = self.model(X)

        # Inverse transform
        predictions = self.scaler.inverse_transform(predictions_scaled.numpy())

        # Return requested horizon
        return predictions[0, :horizon_steps]

    def detect_storm(
        self,
        data: pd.DataFrame,
        current_index: int,
        forecast: Optional[np.ndarray] = None,
        threshold: float = 1500.0
    ) -> bool:
        """
        Detect if storm is predicted

        Args:
            data: Historical data
            current_index: Current index
            forecast: Optional pre-computed forecast
            threshold: Inflow threshold for storm (m³/15min)

        Returns:
            True if storm detected in forecast
        """
        if forecast is None:
            forecast = self.predict(data, current_index, horizon_steps=24)

        # Check if any forecast value exceeds threshold
        return np.any(forecast > threshold)

    def save_model(self, path: str):
        """Save model and scalers"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'feature_scaler': self.feature_scaler,
            'lookback_steps': self.lookback_steps,
            'forecast_horizon': self.forecast_horizon
        }, path)

        print(f"✓ Model saved to {path}")

    def load_model(self, path: str):
        """Load model and scalers"""
        checkpoint = torch.load(path, weights_only=False)

        input_size = checkpoint['feature_scaler'].n_features_in_

        self.model = LSTMInflowForecaster(
            input_size=input_size,
            hidden_size=64,
            num_layers=2,
            output_size=checkpoint['forecast_horizon'],
            dropout=0.2
        )

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.scaler = checkpoint['scaler']
        self.feature_scaler = checkpoint['feature_scaler']
        self.lookback_steps = checkpoint['lookback_steps']
        self.forecast_horizon = checkpoint['forecast_horizon']

        self.model.eval()
        print(f"✓ Model loaded from {path}")


if __name__ == "__main__":
    """Train and test the forecaster"""

    print("="*60)
    print("LSTM Inflow Forecasting - Training")
    print("="*60)
    print()

    # Load data
    print("Loading historical data...")
    loader = HSYDataLoader()
    data_dict = loader.load_all_data()
    data = data_dict['operational_data']

    print(f"Data: {len(data)} timesteps from {data['Time stamp'].min()} to {data['Time stamp'].max()}")

    # Create forecaster
    forecaster = InflowForecastingSystem(
        lookback_steps=48,  # 12 hours history
        forecast_horizon=24  # 6 hours ahead
    )

    # Train model
    forecaster.train(data, epochs=50, batch_size=32, learning_rate=0.001)

    # Save model
    model_path = Path(__file__).parent / 'inflow_lstm_model.pth'
    forecaster.save_model(str(model_path))

    # Test predictions
    print("\n" + "="*60)
    print("Testing Predictions")
    print("="*60)

    test_indices = [500, 700, 900, 1100]

    for idx in test_indices:
        forecast = forecaster.predict(data, idx, horizon_steps=24)
        actual = data['F1'].iloc[idx + 1:idx + 25].values

        # Calculate error
        mae = np.mean(np.abs(forecast - actual))

        # Check storm
        is_storm = forecaster.detect_storm(data, idx, forecast)

        print(f"\nIndex {idx} ({data['Time stamp'].iloc[idx]}):")
        print(f"  Current inflow: {data['F1'].iloc[idx]:.0f} m³/15min")
        print(f"  Forecast (next 6h): {forecast[:4]} ...")
        print(f"  Actual (next 6h): {actual[:4]} ...")
        print(f"  MAE: {mae:.2f} m³/15min")
        print(f"  Storm detected: {is_storm}")

    print("\n✓ Training and testing complete!")

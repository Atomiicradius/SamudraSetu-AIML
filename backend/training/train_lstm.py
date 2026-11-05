import numpy as np
import json
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Set seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)

class FreightLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, output_dim=4, dropout=0.2):
        super(FreightLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_dim)
        )
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        out, (hn, cn) = self.lstm(x)
        # Use last timestep hidden state
        last_hidden = out[:, -1, :]
        out = self.fc(last_hidden)
        return out

def compute_smape(y_true, y_pred):
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    diff = np.abs(y_true - y_pred) / np.maximum(denominator, 1e-8)
    return np.mean(diff) * 100.0

def train_lstm():
    print("=== Training PyTorch LSTM Multi-Horizon Freight Forecasting Model ===")
    
    # Load dataset
    data = np.load('dataset_lstm_master.npz')
    X = data['X']        # Shape: (N, seq_len, input_dim)
    Y_7 = data['Y_7']    # Shape: (N,)
    Y_14 = data['Y_14']
    Y_30 = data['Y_30']
    Y_60 = data['Y_60']
    
    # Combine multi-horizon targets: shape (N, 4) -> [7d, 14d, 30d, 60d]
    Y = np.column_stack([Y_7, Y_14, Y_30, Y_60])
    
    with open('lstm_metadata.json', 'r') as f:
        meta = json.load(f)
        
    num_cols = meta['num_cols']
    target_col = meta['target_col']
    target_col_idx = num_cols.index(target_col)
    scale_factor = meta['scaler_scale'][target_col_idx]
    mean_factor = meta['scaler_mean'][target_col_idx]
    
    # Chronological Split (80% Train, 20% Out-of-sample Test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    Y_train, Y_test = Y[:split_idx], Y[split_idx:]
    
    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    print(f"Input shape: {X_train.shape}, Target shape: {Y_train.shape}")
    
    # Create DataLoaders
    train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(Y_train, dtype=torch.float32))
    test_ds = TensorDataset(torch.tensor(X_test, dtype=torch.float32), torch.tensor(Y_test, dtype=torch.float32))
    
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)
    
    # Initialize Model
    input_dim = X.shape[2]
    model = FreightLSTM(input_dim=input_dim, hidden_dim=64, num_layers=2, output_dim=4, dropout=0.2)
    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    epochs = 40
    train_losses, val_losses = [], []
    
    for epoch in range(1, epochs + 1):
        model.train()
        running_train_loss = 0.0
        for bx, by in train_loader:
            optimizer.zero_grad()
            pred = model(bx)
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()
            running_train_loss += loss.item() * bx.size(0)
            
        epoch_train_loss = running_train_loss / len(X_train)
        
        # Validation
        model.eval()
        running_val_loss = 0.0
        with torch.no_grad():
            for bx, by in test_loader:
                pred = model(bx)
                loss = criterion(pred, by)
                running_val_loss += loss.item() * bx.size(0)
                
        epoch_val_loss = running_val_loss / len(X_test)
        scheduler.step(epoch_val_loss)
        
        train_losses.append(epoch_train_loss)
        val_losses.append(epoch_val_loss)
        
        if epoch % 5 == 0 or epoch == epochs:
            print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {epoch_train_loss:.5f} | Test Loss: {epoch_val_loss:.5f}")
            
    # Save Model Weights
    torch.save(model.state_dict(), 'lstm_freight_model.pth')
    
    # Evaluate Out-of-Sample Predictions
    model.eval()
    with torch.no_grad():
        test_pred_scaled = model(torch.tensor(X_test, dtype=torch.float32)).numpy()
        
    # Unscale predictions & targets back to original USD/MT units
    Y_test_unscaled = Y_test * scale_factor + mean_factor
    test_pred_unscaled = test_pred_scaled * scale_factor + mean_factor
    
    horizons = ['7-Day', '14-Day', '30-Day', '60-Day']
    results = {}
    
    print("\n--- Out-of-Sample Evaluation Across Horizons ---")
    for i, h in enumerate(horizons):
        y_t = Y_test_unscaled[:, i]
        y_p = test_pred_unscaled[:, i]
        
        mae = mean_absolute_error(y_t, y_p)
        rmse = np.sqrt(mean_squared_error(y_t, y_p))
        smape = compute_smape(y_t, y_p)
        
        # Directional Accuracy
        y_t_diff = np.diff(y_t)
        y_p_diff = np.diff(y_p)
        dir_acc = np.mean(np.sign(y_t_diff) == np.sign(y_p_diff)) * 100.0
        
        print(f"Horizon: {h:<6} | MAE: ${mae:.2f}/MT | RMSE: ${rmse:.2f}/MT | sMAPE: {smape:.2f}% | Dir Acc: {dir_acc:.2f}%")
        
        results[h] = {
            'mae_usd_per_mt': float(mae),
            'rmse_usd_per_mt': float(rmse),
            'smape_pct': float(smape),
            'directional_accuracy_pct': float(dir_acc)
        }
        
    with open('lstm_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    # Plot Training & Validation Loss
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, epochs + 1), train_losses, label='Train Loss', color='#1f77b4', linewidth=2)
    plt.plot(range(1, epochs + 1), val_losses, label='Test Loss', color='#d62728', linestyle='--', linewidth=2)
    plt.title('PyTorch LSTM Training & Out-of-Sample Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Smooth L1 Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('lstm_loss_curve.png', dpi=300)
    plt.close()
    
    # Plot Multi-Horizon Predictions vs Actuals
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), sharex=True)
    axes = axes.flatten()
    
    for i, h in enumerate(horizons):
        axes[i].plot(Y_test_unscaled[:, i], label='Actual Rate (USD/MT)', color='#1f77b4', alpha=0.8)
        axes[i].plot(test_pred_unscaled[:, i], label=f'LSTM {h} Forecast', color='#2ca02c', linestyle='--')
        axes[i].set_title(f'LSTM Forecast ({h} Horizon) vs Actual Freight Rate')
        axes[i].set_ylabel('USD / Metric Tonne')
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)
        
    plt.xlabel('Test Set Timesteps')
    plt.tight_layout()
    plt.savefig('lstm_multi_horizon_forecast.png', dpi=300)
    plt.close()
    
    print("\nPyTorch LSTM Training & Evaluation Complete. Saved weights, results, and loss plots.")

if __name__ == '__main__':
    train_lstm()

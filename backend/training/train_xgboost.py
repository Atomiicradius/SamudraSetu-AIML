import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json

def train_xgboost():
    print("=== Training XGBoost Models ===")
    
    # Load dataset
    df = pd.read_csv('dataset_xgboost_master.csv')
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by='date', inplace=True)
    
    # Identify non-feature columns
    ignore_cols = ['date', 'port_code', 'route_id']
    
    # Target columns to model
    target_cols = {
        'congestion_index_0_100': 'Port Congestion Index (0-100)',
        'sim_wait_hours': 'Vessel Wait Hours',
        'freight_australia_paradip_supramax_usd_per_mt': 'Freight Rate (USD/MT)'
    }
    
    # Chronological Split (Train: before 2025-10-01, Test: Oct-Dec 2025)
    split_date = pd.to_datetime('2025-10-01')
    train_mask = df['date'] < split_date
    test_mask = df['date'] >= split_date
    
    results = {}
    
    for target_col, target_label in target_cols.items():
        if target_col not in df.columns:
            print(f"Skipping {target_col} (not found in dataset)")
            continue
            
        print(f"\n--- Training XGBoost for Target: {target_label} ({target_col}) ---")
        
        feature_cols = [c for c in df.columns if c not in ignore_cols and c not in target_cols.keys()]
        
        X_train = df.loc[train_mask, feature_cols]
        y_train = df.loc[train_mask, target_col]
        X_test = df.loc[test_mask, feature_cols]
        y_test = df.loc[test_mask, target_col]
        
        # Instantiate XGBoost Regressor
        model = xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.03,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train), (X_test, y_test)],
            verbose=False
        )
        
        # Save model
        model.save_model(f'xgboost_model_{target_col}.json')
        
        # Predictions
        y_pred = model.predict(X_test)
        
        # Evaluation Metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Directional Accuracy (Direction of change matched)
        y_test_diff = np.diff(y_test)
        y_pred_diff = np.diff(y_pred)
        dir_acc = np.mean(np.sign(y_test_diff) == np.sign(y_pred_diff)) * 100.0
        
        print(f"Test MAE:  {mae:.4f}")
        print(f"Test RMSE: {rmse:.4f}")
        print(f"Test R^2:  {r2:.4f}")
        print(f"Directional Accuracy: {dir_acc:.2f}%")
        
        results[target_col] = {
            'target_name': target_label,
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'directional_accuracy_pct': float(dir_acc)
        }
        
        # Plot Predictions vs Actuals
        plt.figure(figsize=(12, 5))
        test_dates = df.loc[test_mask, 'date']
        plt.plot(test_dates, y_test, label='Actual', color='#1f77b4', linewidth=2)
        plt.plot(test_dates, y_pred, label='XGBoost Predicted', color='#ff7f0e', linestyle='--', linewidth=2)
        plt.title(f'XGBoost Forecast vs Actual: {target_label} (Out-of-Sample Test Set)')
        plt.xlabel('Date')
        plt.ylabel(target_label)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plot_path = f'xgboost_pred_{target_col}.png'
        plt.savefig(plot_path, dpi=300)
        plt.close()
        
        # Plot Top 15 Feature Importances
        importance = model.feature_importances_
        top_idx = np.argsort(importance)[-15:]
        
        plt.figure(figsize=(10, 6))
        plt.barh(range(len(top_idx)), importance[top_idx], align='center', color='#2ca02c')
        plt.yticks(range(len(top_idx)), [feature_cols[i] for i in top_idx])
        plt.xlabel('Feature Importance (Gain)')
        plt.title(f'Top 15 Feature Importances: XGBoost ({target_label})')
        plt.tight_layout()
        plt.savefig(f'xgboost_importance_{target_col}.png', dpi=300)
        plt.close()
        
    with open('xgboost_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print("\nXGBoost Training Complete. Saved models, metrics, and plots.")

if __name__ == '__main__':
    train_xgboost()

import json
import pandas as pd
import numpy as np

def generate_model_benchmark():
    print("=== Generating Model Comparison Benchmark ===")
    
    # Load XGBoost Results
    with open('xgboost_results.json', 'r') as f:
        xgb_res = json.load(f)
        
    # Load LSTM Results
    with open('lstm_results.json', 'r') as f:
        lstm_res = json.load(f)
        
    benchmark_rows = []
    
    # Add XGBoost Rows
    for target_key, res in xgb_res.items():
        benchmark_rows.append({
            'Model Architecture': 'XGBoost Regressor',
            'Target / Task': res['target_name'],
            'Horizon': '1-Day Ahead',
            'MAE': f"{res['mae']:.4f}",
            'RMSE': f"{res['rmse']:.4f}",
            'sMAPE / R^2': f"R^2 = {res['r2']:.4f}",
            'Directional Accuracy': f"{res['directional_accuracy_pct']:.2f}%"
        })
        
    # Add LSTM Rows
    for horizon, res in lstm_res.items():
        benchmark_rows.append({
            'Model Architecture': 'PyTorch 2-Layer LSTM',
            'Target / Task': 'Freight Rate (USD/MT)',
            'Horizon': horizon,
            'MAE': f"${res['mae_usd_per_mt']:.2f}/MT",
            'RMSE': f"${res['rmse_usd_per_mt']:.2f}/MT",
            'sMAPE / R^2': f"sMAPE = {res['smape_pct']:.2f}%",
            'Directional Accuracy': f"{res['directional_accuracy_pct']:.2f}%"
        })
        
    df_benchmark = pd.DataFrame(benchmark_rows)
    print("\n" + df_benchmark.to_string(index=False))
    
    df_benchmark.to_csv('model_benchmark_summary.csv', index=False)
    print("\nSaved benchmark summary to model_benchmark_summary.csv")

if __name__ == '__main__':
    generate_model_benchmark()

import pandas as pd
import numpy as np
import json
import os
from sklearn.preprocessing import StandardScaler

def build_xgboost_master():
    print("Building XGBoost Model-Ready Master Dataset (dataset_xgboost_master.csv)...")
    
    df = pd.read_csv('master_port_ml_dataset.csv')
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by=['port_code', 'date'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # 1. Forward-fill market / macro variables per rules
    macro_cols = [
        'usd_inr_exchange_rate', 'brent_crude_usd_per_bbl', 'coal_price_usd_per_mt',
        'freight_aus_to_paradip_capesize_usd_per_mt', 'freight_aus_to_paradip_panamax_usd_per_mt',
        'freight_usa_to_vizag_capesize_usd_per_mt', 'freight_moz_to_dhamra_supramax_usd_per_mt',
        'freight_australia_paradip_supramax_usd_per_mt', 'freight_indonesia_visakhapatnam_panamax_usd_per_mt',
        'freight_mozambique_dhamra_handysize_usd_per_mt'
    ]
    
    existing_macro_cols = [c for c in macro_cols if c in df.columns]
    df[existing_macro_cols] = df[existing_macro_cols].ffill().bfill()
    
    # 2. Add Cyclical Calendar Features
    df['day_of_year'] = df['date'].dt.dayofyear
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    df['day_of_week'] = df['date'].dt.dayofweek
    
    df['sin_day_of_year'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    df['cos_day_of_year'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12.0)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12.0)
    
    # 3. Create Lag Features & Rolling Statistics per Port
    lag_cols = ['congestion_index_0_100', 'sim_wait_hours', 'sim_anchorage_count', 'disruption_risk_pct'] + existing_macro_cols
    lag_days = [1, 3, 7, 14, 30]
    
    dfs_by_port = []
    for port_code, group in df.groupby('port_code'):
        group = group.copy()
        new_cols = {}
        for col in lag_cols:
            if col in group.columns:
                for lag in lag_days:
                    new_cols[f'{col}_lag_{lag}d'] = group[col].shift(lag)
                
                # Rolling statistics
                new_cols[f'{col}_roll_mean_7d'] = group[col].shift(1).rolling(window=7, min_periods=1).mean()
                new_cols[f'{col}_roll_std_7d'] = group[col].shift(1).rolling(window=7, min_periods=1).std().fillna(0)
                new_cols[f'{col}_roll_mean_30d'] = group[col].shift(1).rolling(window=30, min_periods=1).mean()
                new_cols[f'{col}_roll_std_30d'] = group[col].shift(1).rolling(window=30, min_periods=1).std().fillna(0)
        
        new_df = pd.DataFrame(new_cols, index=group.index)
        group = pd.concat([group, new_df], axis=1)
        dfs_by_port.append(group)
        
    df_xgb = pd.concat(dfs_by_port, ignore_index=True)
    
    # 4. One-Hot Encode Categorical Columns
    cat_cols = ['port_name', 'vessel_class_reference']
    existing_cat = [c for c in cat_cols if c in df_xgb.columns]
    df_xgb = pd.get_dummies(df_xgb, columns=existing_cat, drop_first=False)
    
    # Forward fill / backward fill any remaining NaNs from shifting
    df_xgb.ffill(inplace=True)
    df_xgb.bfill(inplace=True)
    
    output_path = 'dataset_xgboost_master.csv'
    df_xgb.to_csv(output_path, index=False)
    print(f"SUCCESS: Exported {output_path} ({df_xgb.shape[0]} rows, {df_xgb.shape[1]} columns)")
    return df_xgb


def build_lstm_master(lookback=30):
    print(f"Building LSTM Sequential Model Dataset (lookback={lookback} days)...")
    
    df = pd.read_csv('master_macro_freight_daily.csv')
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by='date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Fill missing values
    num_cols = [c for c in df.columns if c != 'date']
    df[num_cols] = df[num_cols].ffill().bfill()
    
    # Normalize features using StandardScaler
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[num_cols])
    
    X, Y_7, Y_14, Y_30, Y_60 = [], [], [], [], []
    
    target_col_idx = 0
    if 'freight_aus_to_paradip_capesize_usd_per_mt' in num_cols:
        target_col_idx = num_cols.index('freight_aus_to_paradip_capesize_usd_per_mt')
    
    max_horizon = 60
    for i in range(lookback, len(scaled_features) - max_horizon):
        X.append(scaled_features[i - lookback:i])
        Y_7.append(scaled_features[i + 7 - 1, target_col_idx])
        Y_14.append(scaled_features[i + 14 - 1, target_col_idx])
        Y_30.append(scaled_features[i + 30 - 1, target_col_idx])
        Y_60.append(scaled_features[i + 60 - 1, target_col_idx])
        
    X = np.array(X)
    Y_7 = np.array(Y_7)
    Y_14 = np.array(Y_14)
    Y_30 = np.array(Y_30)
    Y_60 = np.array(Y_60)
    
    output_npz = 'dataset_lstm_master.npz'
    np.savez_compressed(output_npz, X=X, Y_7=Y_7, Y_14=Y_14, Y_30=Y_30, Y_60=Y_60)
    
    metadata = {
        'num_cols': num_cols,
        'target_col': num_cols[target_col_idx],
        'lookback_days': lookback,
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist(),
        'X_shape': list(X.shape),
        'Y_7_shape': list(Y_7.shape),
        'Y_14_shape': list(Y_14.shape),
        'Y_30_shape': list(Y_30.shape),
        'Y_60_shape': list(Y_60.shape),
    }
    
    with open('lstm_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"SUCCESS: Exported {output_npz} with X shape {X.shape} and metadata stored in lstm_metadata.json")

if __name__ == '__main__':
    build_xgboost_master()
    build_lstm_master(lookback=30)

import pandas as pd
import os

def run_merge():
    print("Starting data merge process...")
    
    # 1. Load Macro Data
    print("Loading raw_commodity_macro.csv...")
    df_macro = pd.read_csv('raw_commodity_macro.csv')
    df_macro['date'] = pd.to_datetime(df_macro['date']).dt.strftime('%Y-%m-%d')

    # 2. Load Generated Freight Routes Data
    print("Loading raw_freight_routes.csv...")
    df_rfr = pd.read_csv('raw_freight_routes.csv')
    df_rfr['date'] = pd.to_datetime(df_rfr['date']).dt.strftime('%Y-%m-%d')

    # 3. Load Freight Rates Data & Pivot
    print("Loading freight_rates.csv...")
    df_fr = pd.read_csv('freight_rates.csv')
    df_fr['date'] = pd.to_datetime(df_fr['date']).dt.strftime('%Y-%m-%d')
    fr_pivoted = df_fr.pivot_table(index='date', columns=['route', 'vessel_class'], values='rate_usd_per_mt')
    fr_pivoted.columns = [f"freight_{r.replace('-', '_').lower()}_{v.lower()}_usd_per_mt" for r, v in fr_pivoted.columns]
    fr_pivoted.reset_index(inplace=True)

    # 4. Load Port ML Training Data (prefers ML_Ready_Dataset.xlsx if present, falls back to Port_data.xlsx)
    port_excel = 'ML_Ready_Dataset.xlsx' if os.path.exists('ML_Ready_Dataset.xlsx') else 'Port_data.xlsx'
    print(f"Loading port training data from {port_excel} (sheet ML_Training_Data)...")
    df_ml = pd.read_excel(port_excel, sheet_name='ML_Training_Data', header=3)
    df_ml['date'] = pd.to_datetime(df_ml['date']).dt.strftime('%Y-%m-%d')

    # 5. Merge Daily Macro & Freight Time Series
    print("Merging daily macro & freight time series...")
    df_master = pd.merge(df_macro, df_rfr, on='date', how='left')
    df_master = pd.merge(df_master, fr_pivoted, on='date', how='left')
    df_master.to_csv('master_macro_freight_daily.csv', index=False)

    # 6. Merge Port Dataset with Time Series Master
    print("Merging port dataset with time series master...")
    df_port_master = pd.merge(df_ml, df_master, on='date', how='left')
    df_port_master.to_csv('master_port_ml_dataset.csv', index=False)

    print("SUCCESS: Generated master_port_ml_dataset.csv and master_macro_freight_daily.csv")
    print(f"master_macro_freight_daily shape: {df_master.shape}")
    print(f"master_port_ml_dataset shape: {df_port_master.shape}")

if __name__ == '__main__':
    run_merge()

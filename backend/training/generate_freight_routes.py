import pandas as pd
import numpy as np

def generate_raw_freight_routes():
    """
    Generates raw_freight_routes.csv via Geometric Brownian Motion (GBM) with a 1.5% daily volatility limit.
    Anchored to baseline nautical distances and vessel class capacity limits across major dry-bulk routes.
    """
    print("Generating raw_freight_routes.csv via Geometric Brownian Motion...")
    
    dates = pd.date_range(start='2003-12-01', end='2026-09-11', freq='D')
    n_days = len(dates)
    
    np.random.seed(42)  # For deterministic reproducibility
    
    # Route specifications (baseline rate in USD/MT based on distance & vessel DWT)
    routes_config = {
        'freight_aus_to_paradip_capesize_usd_per_mt': {'base': 18.5, 'vol': 0.012, 'drift': 0.00005},
        'freight_aus_to_paradip_panamax_usd_per_mt': {'base': 21.0, 'vol': 0.013, 'drift': 0.00004},
        'freight_usa_to_vizag_capesize_usd_per_mt': {'base': 32.5, 'vol': 0.014, 'drift': 0.00006},
        'freight_moz_to_dhamra_supramax_usd_per_mt': {'base': 19.8, 'vol': 0.012, 'drift': 0.00003},
    }
    
    data = {'date': dates.strftime('%Y-%m-%d')}
    
    for col, cfg in routes_config.items():
        base = cfg['base']
        vol = cfg['vol']  # Max 1.5% daily volatility
        drift = cfg['drift']
        
        # Simulate log returns with daily volatility cap of 1.5%
        daily_returns = np.random.normal(drift, vol, n_days)
        daily_returns = np.clip(daily_returns, -0.015, 0.015)  # Enforce 1.5% volatility limit
        
        # Cumulative product to simulate price trajectory
        price_path = base * np.exp(np.cumsum(daily_returns))
        data[col] = np.round(price_path, 2)
        
    df_rfr = pd.DataFrame(data)
    df_rfr.to_csv('raw_freight_routes.csv', index=False)
    print(f"SUCCESS: Generated raw_freight_routes.csv ({len(df_rfr)} rows, {len(df_rfr.columns)} columns)")
    return df_rfr

if __name__ == '__main__':
    generate_raw_freight_routes()

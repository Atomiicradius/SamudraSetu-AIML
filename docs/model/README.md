# SamudraSetu: Intelligent Maritime Freight Forecasting & Port Optimization Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange.svg)](https://xgboost.readthedocs.io/)
[![PyTorch](https://img.shields.io/badge/Deep%20Learning-PyTorch-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**SamudraSetu** is an end-to-end intelligent maritime freight forecasting and port congestion prediction platform built for **Smart India Hackathon (SIH 2026 - Problem Statement 26006)** under the **Ministry of Steel (SAIL)**. 

The system transitions bulk cargo procurement from reactive spot-market purchasing to proactive, data-driven chartering strategies across major Indian East Coast trade corridors (e.g. Australia to Paradip, Mozambique to Dhamra, Indonesia to Visakhapatnam).

---

## 🌟 Key Capabilities

1. **Port Congestion & Delays Prediction (XGBoost Regressor)**:
   - Predicts 1-day ahead port congestion indices ($0–100$) and anchorage turnaround waiting times (`sim_wait_hours`) across Paradip and Newcastle ports.
   - **Performance**: Achieves **64.1% $R^2$** and **69.95% Directional Accuracy** for port congestion.

2. **Multi-Horizon Spot Freight Forecasting (PyTorch LSTM)**:
   - Deep learning 2-layer LSTM model with sliding lookback windows forecasting bulk freight spot rates across **7-day**, **14-day**, **30-day**, and **60-day** contract horizons.
   - **Performance**: Achieves **$3.67 to $3.74/MT MAE** and **~21.1% sMAPE** across multi-horizon forecasts.

3. **Master Feature Engineering & Data Pipeline**:
   - Automated ingestion, forward-fill market index imputation (`ffill()`), temporal lag features (`1d, 3d, 7d, 14d, 30d`), rolling statistics (`7d, 30d mean/std`), and cyclical calendar encodings (`sin/cos` day of year).

---

## 📊 Quantitative Model Benchmark Summary

| Model Architecture | Target Task | Horizon | MAE | RMSE | $R^2$ / sMAPE | Directional Accuracy |
|---|---|---|---|---|---|---|
| **XGBoost Regressor** | Port Congestion Index ($0–100$) | 1-Day Ahead | **1.7298** | **3.0043** | **$R^2 = 0.6413$** | **69.95%** |
| **XGBoost Regressor** | Vessel Wait Hours (`sim_wait_hours`) | 1-Day Ahead | **1.0848 hrs** | **1.8120 hrs** | **$R^2 = 0.2904$** | **68.85%** |
| **PyTorch 2-Layer LSTM** | Freight Spot Rate (`USD/MT`) | 7-Day Horizon | **$3.74/MT** | **$4.09/MT** | **$\text{sMAPE} = 21.53\%$** | **47.56%** |
| **PyTorch 2-Layer LSTM** | Freight Spot Rate (`USD/MT`) | 14-Day Horizon | **$3.67/MT** | **$4.01/MT** | **$\text{sMAPE} = 21.16\%$** | **48.33%** |
| **PyTorch 2-Layer LSTM** | Freight Spot Rate (`USD/MT`) | 30-Day Horizon | **$3.72/MT** | **$4.02/MT** | **$\text{sMAPE} = 21.45\%$** | **52.01%** |
| **PyTorch 2-Layer LSTM** | Freight Spot Rate (`USD/MT`) | 60-Day Horizon | **$3.71/MT** | **$3.98/MT** | **$\text{sMAPE} = 21.46\%$** | **47.13%** |

---

## 📁 Repository Directory & Master Datasets

> **Note**: In accordance with project specifications, raw source files are excluded from git tracking. Only standardized **Master Datasets** and preprocessed model matrices are committed.

```text
SamudraSetu/
├── generate_freight_routes.py      # Synthesizes proxy route freight indices via Geometric Brownian Motion
├── merge_all_data.py               # Merges macro, route indices, spot rates, and port training sheets
├── build_master_datasets.py        # Engineers lag/rolling features for XGBoost & 3D lookback tensors for LSTM
├── train_xgboost.py                # Trains XGBoost regressors for port congestion and wait times
├── train_lstm.py                   # Trains PyTorch 2-layer LSTM for multi-horizon freight rate forecasting
├── evaluate_models.py              # Computes comparative benchmark metrics and outputs model_benchmark_summary.csv
│
├── master_macro_freight_daily.csv  # Combined daily market base (5,937 rows x 11 columns, 2003-2026)
├── master_port_ml_dataset.csv      # Merged port ML dataset (730 rows x 43 columns, Newcastle & Paradip)
├── dataset_xgboost_master.csv      # Tabular feature matrix (730 rows x 176 columns) with lags & rolling stats
├── dataset_lstm_master.npz         # Scaled 3D sequential tensors (5847, 30, 10) for PyTorch LSTM
├── lstm_metadata.json              # StandardScaler means, scales, and sequence target metadata
│
├── xgboost_model_*.json            # Trained XGBoost model binaries
├── lstm_freight_model.pth          # PyTorch trained LSTM state weights
├── *.png                           # Out-of-sample forecast charts & feature importance bar plots
└── model_benchmark_summary.csv     # Full benchmark comparison table
```

---

## 🚀 Quickstart & Reproduction Guide

### 1. Requirements & Setup

Ensure Python 3.10+ is installed along with required packages:

```bash
pip install pandas numpy scikit-learn xgboost torch matplotlib openpyxl
```

### 2. Generate Master Datasets

Step 1: Synthesize proxy route indices and merge raw sources:
```bash
python generate_freight_routes.py
python merge_all_data.py
```
*Output*: Generates `master_macro_freight_daily.csv` and `master_port_ml_dataset.csv`.

Step 2: Build model-ready matrices:
```bash
python build_master_datasets.py
```
*Output*: Generates `dataset_xgboost_master.csv` (176 features) and `dataset_lstm_master.npz`.

### 3. Model Training & Evaluation

Train the XGBoost models:
```bash
python train_xgboost.py
```

Train the PyTorch Multi-Horizon LSTM:
```bash
python train_lstm.py
```

Run the benchmark evaluation:
```bash
python evaluate_models.py
```

---

## 📈 Visualizations & Plots

- **PyTorch LSTM Out-of-Sample Forecast**: `lstm_multi_horizon_forecast.png`
- **PyTorch LSTM Loss Curve**: `lstm_loss_curve.png`
- **XGBoost Congestion Forecast**: `xgboost_pred_congestion_index_0_100.png`
- **XGBoost Feature Importance**: `xgboost_importance_congestion_index_0_100.png`

---

## 🛡️ License & Acknowledgments

Developed for **Smart India Hackathon (SIH 2026)** — **Problem Statement 26006 (Ministry of Steel / SAIL)**.
Licensed under the [MIT License](LICENSE).

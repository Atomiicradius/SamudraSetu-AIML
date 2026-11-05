# Historical training and dataset-build scripts

These scripts came from the model repository and are retained for provenance
and reproduction. The committed serving path does **not** retrain models; it
loads the artifacts in `backend/artifacts/` through `backend/model_service.py`.

The original scripts assume their inputs and outputs are in the current
working directory. To reproduce them without editing the scripts, run them
from `data/model/` and provide/copy the script there, or update their paths in a
separate training-focused change. `merge_all_data.py` additionally requires
raw files that were not committed by Repo B (`raw_commodity_macro.csv`,
`raw_freight_routes.csv`, `freight_rates.csv`, and a port workbook).

Known methodological issue: `build_master_datasets.py` uses backward-fill and
fits `StandardScaler` before the chronological split. That leaks future
distribution information and conflicts with `context/model.md`. The existing
weights are preserved so the two repositories can be integrated and tested,
but should be retrained with train-only scaling and strict
`available_as_of <= decision_timestamp` feature construction before any
production claim.


# ML Prep

## Supervised dataset

```python
from metdatapy.mlprep import make_supervised
sup = make_supervised(df, targets=["temp_c"], horizons=[1, 3], lags=[1,2,3])
```

Adds `{col}_lag{n}` for numeric columns and targets like `temp_c_t+1`.

## Time-safe splits

```python
from metdatapy.mlprep import time_split
splits = time_split(sup, train_end=pd.Timestamp("2025-01-15T00:00Z"))
```

## Scaling

```python
from metdatapy.mlprep import fit_scaler, apply_scaler
scaler = fit_scaler(splits["train"], method="standard")
train_scaled = apply_scaler(splits["train"], scaler)
val_scaled = apply_scaler(splits["val"], scaler)
test_scaled = apply_scaler(splits["test"], scaler)
```


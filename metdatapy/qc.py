from typing import Dict
import pandas as pd

from .utils import PLAUSIBLE_BOUNDS

def qc_range(df: pd.DataFrame) -> pd.DataFrame:
    for var, (lo, hi) in PLAUSIBLE_BOUNDS.items():
        if var in df.columns:
            flag_col = f"qc_{var}_range"
            vals = df[var]
            df[flag_col] = (vals < lo) | (vals > hi)
    return df



 from typing import Optional
 import pandas as pd

 def read_csv(path: str, ts_col: Optional[str] = None) -> pd.DataFrame:
     df = pd.read_csv(path)
     if ts_col and ts_col in df.columns:
         df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
     return df

 def read_parquet(path: str) -> pd.DataFrame:
     return pd.read_parquet(path)

 def to_parquet(df: pd.DataFrame, path: str) -> None:
     df.to_parquet(path, index=True)



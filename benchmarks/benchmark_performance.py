"""
Performance benchmarks for MetDataPy operations.

Demonstrates computational efficiency for common meteorological data processing tasks.
"""
import time
import pandas as pd
import numpy as np
from metdatapy.core import WeatherSet
from metdatapy.mlprep import make_supervised, time_split, fit_scaler, apply_scaler

def benchmark_operation(name, func, *args, **kwargs):
    """Benchmark a single operation."""
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    return elapsed, result


def run_benchmarks():
    """Run comprehensive performance benchmarks."""
    print("=" * 70)
    print("MetDataPy Performance Benchmarks")
    print("=" * 70)
    
    # Create test datasets of varying sizes
    sizes = {
        'Small': 1_000,      # ~1 week of 10-min data
        'Medium': 10_000,    # ~2.5 months of 10-min data
        'Large': 52_560,     # 1 year of 10-min data
        'XLarge': 100_000,   # ~2 years of 10-min data
    }
    
    results = {}
    
    for size_name, n_rows in sizes.items():
        print(f"\n{size_name} Dataset ({n_rows:,} rows)")
        print("-" * 70)
        
        # Generate synthetic data
        df = pd.DataFrame({
            'ts_utc': pd.date_range('2024-01-01', periods=n_rows, freq='10min', tz='UTC'),
            'temp_c': np.random.normal(20, 5, n_rows),
            'rh_pct': np.random.uniform(40, 90, n_rows),
            'pres_hpa': np.random.normal(1013, 10, n_rows),
            'wspd_ms': np.random.gamma(2, 2, n_rows),
            'wdir_deg': np.random.uniform(0, 360, n_rows),
            'rain_mm': np.random.exponential(0.1, n_rows),
        }).set_index('ts_utc')
        
        size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        print(f"Memory size: {size_mb:.2f} MB")
        
        results[size_name] = {}
        
        # Benchmark 1: Quality Control
        ws = WeatherSet(df.copy())
        t, ws = benchmark_operation("QC (range + spike + flatline)", 
                                     lambda: ws.qc_range().qc_spike().qc_flatline())
        results[size_name]['qc'] = t
        print(f"  QC operations:        {t:.3f}s ({n_rows/t:,.0f} rows/s)")
        
        # Benchmark 2: Derived Metrics
        ws = WeatherSet(df.copy())
        t, ws = benchmark_operation("Derived metrics", 
                                     lambda: ws.derive(['dew_point', 'vpd', 'heat_index', 'wind_chill']))
        results[size_name]['derive'] = t
        print(f"  Derived metrics:      {t:.3f}s ({n_rows/t:,.0f} rows/s)")
        
        # Benchmark 3: Resampling
        ws = WeatherSet(df.copy())
        t, ws = benchmark_operation("Resample to hourly", 
                                     lambda: ws.resample('1h'))
        results[size_name]['resample'] = t
        print(f"  Resample (10min->1h): {t:.3f}s ({n_rows/t:,.0f} rows/s)")
        
        # Benchmark 4: Calendar Features
        ws = WeatherSet(df.copy())
        t, ws = benchmark_operation("Calendar features", 
                                     lambda: ws.calendar_features(cyclical=True))
        results[size_name]['calendar'] = t
        print(f"  Calendar features:    {t:.3f}s ({n_rows/t:,.0f} rows/s)")
        
        # Benchmark 5: ML Preparation (for medium and large only)
        if n_rows >= 10_000:
            t, sup = benchmark_operation("Supervised table", 
                                         make_supervised, df.copy(), 
                                         targets=['temp_c'], lags=[1,2,3,6,12], horizons=[1,3,6])
            results[size_name]['ml_prep'] = t
            print(f"  ML supervised table:  {t:.3f}s ({n_rows/t:,.0f} rows/s)")
            
            # Benchmark 6: Scaling
            t, scaler = benchmark_operation("Fit scaler", 
                                            fit_scaler, sup, method='standard')
            results[size_name]['fit_scaler'] = t
            print(f"  Fit scaler:           {t:.3f}s")
            
            t, scaled = benchmark_operation("Apply scaler", 
                                            apply_scaler, sup, scaler)
            results[size_name]['apply_scaler'] = t
            print(f"  Apply scaler:         {t:.3f}s ({len(sup)/t:,.0f} rows/s)")
    
    # Summary
    print("\n" + "=" * 70)
    print("Performance Summary")
    print("=" * 70)
    print("\nTypical throughput for core operations:")
    
    # Calculate median throughput for Large dataset
    large = results['Large']
    print(f"  Quality Control:      ~{sizes['Large']/large['qc']:,.0f} rows/second")
    print(f"  Derived Metrics:      ~{sizes['Large']/large['derive']:,.0f} rows/second")
    print(f"  Resampling:           ~{sizes['Large']/large['resample']:,.0f} rows/second")
    print(f"  Calendar Features:    ~{sizes['Large']/large['calendar']:,.0f} rows/second")
    if 'ml_prep' in large:
        print(f"  ML Preparation:       ~{sizes['Large']/large['ml_prep']:,.0f} rows/second")
    
    print("\nScalability:")
    print(f"  1 year of 10-min data (~52k rows): {sum([large[k] for k in ['qc', 'derive', 'resample', 'calendar']]):.2f}s total")
    
    print("\n" + "=" * 70)
    print("Environment:")
    print(f"  pandas version: {pd.__version__}")
    print(f"  numpy version: {np.__version__}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    results = run_benchmarks()
    print("\n[OK] Benchmarks complete!")


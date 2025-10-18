"""
Generate synthetic weather data for MetDataPy examples and tests.
License: MIT (same as MetDataPy)
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_sample_weather_data(
    start_date="2024-01-01",
    end_date="2024-12-31",
    freq="10min",
    station_name="Sample Station",
    add_gaps=True,
    add_anomalies=True,
    seed=42
):
    """
    Generate realistic synthetic weather data.
    
    Args:
        start_date: Start date string
        end_date: End date string
        freq: Frequency string (e.g., '10min', '1H')
        station_name: Name of the weather station
        add_gaps: If True, introduce random data gaps
        add_anomalies: If True, add spikes, flatlines, and out-of-range values
        seed: Random seed for reproducibility
    
    Returns:
        pd.DataFrame: Synthetic weather data
    """
    np.random.seed(seed)
    
    # Create time index
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    n = len(date_range)
    
    # Generate seasonal temperature pattern (°C)
    day_of_year = date_range.dayofyear
    hour_of_day = date_range.hour + date_range.minute / 60.0
    
    # Base temperature with seasonal variation
    temp_base = 15 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    # Diurnal variation
    temp_diurnal = 5 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
    # Random noise
    temp_noise = np.random.normal(0, 1.5, n)
    temp_c = temp_base + temp_diurnal + temp_noise
    
    # Relative humidity (%) - inversely correlated with temperature
    rh_base = 70 - 0.5 * (temp_c - 15)
    rh_noise = np.random.normal(0, 5, n)
    rh_pct = np.clip(rh_base + rh_noise, 10, 100)
    
    # Atmospheric pressure (hPa) - with slow variations
    pres_base = 1013 + 10 * np.sin(2 * np.pi * day_of_year / 30)
    pres_noise = np.random.normal(0, 2, n)
    pres_hpa = pres_base + pres_noise
    
    # Wind speed (m/s) - log-normal distribution
    wspd_ms = np.random.lognormal(1.0, 0.8, n)
    wspd_ms = np.clip(wspd_ms, 0, 30)
    
    # Wind direction (degrees) - random with some persistence
    wdir_deg = np.zeros(n)
    wdir_deg[0] = np.random.uniform(0, 360)
    for i in range(1, n):
        # Add persistence and random walk
        wdir_deg[i] = (wdir_deg[i-1] + np.random.normal(0, 20)) % 360
    # Set to NaN when wind speed is very low
    wdir_deg[wspd_ms < 0.5] = np.nan
    
    # Wind gust (m/s) - always >= wind speed
    gust_ms = wspd_ms + np.random.exponential(1.5, n)
    gust_ms = np.clip(gust_ms, wspd_ms, 50)
    
    # Rainfall (mm) - occasional events
    rain_mm = np.zeros(n)
    rain_events = np.random.random(n) < 0.05  # 5% chance of rain
    rain_mm[rain_events] = np.random.exponential(2, rain_events.sum())
    rain_mm = np.clip(rain_mm, 0, 50)
    
    # Solar radiation (W/m²) - depends on time of day and season
    solar_potential = np.maximum(0, np.sin(2 * np.pi * (hour_of_day - 6) / 12))
    solar_seasonal = 1 + 0.3 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
    solar_wm2 = 1000 * solar_potential * solar_seasonal
    # Cloud effect (reduced during rain)
    cloud_factor = np.where(rain_mm > 0, 0.3, np.random.uniform(0.7, 1.0, n))
    solar_wm2 = solar_wm2 * cloud_factor
    solar_wm2 = np.clip(solar_wm2, 0, 1200)
    
    # UV index - proportional to solar radiation
    uv_index = solar_wm2 / 100
    uv_index = np.clip(uv_index, 0, 12)
    
    # Create DataFrame
    df = pd.DataFrame({
        "DateTime": date_range,
        "Temperature (°F)": temp_c * 9/5 + 32,  # Store as Fahrenheit to test conversion
        "Relative Humidity (%)": rh_pct,
        "Pressure (mbar)": pres_hpa,
        "Wind Speed (mph)": wspd_ms * 2.23694,  # Store as mph to test conversion
        "Wind Direction (°)": wdir_deg,
        "Wind Gust (mph)": gust_ms * 2.23694,
        "Rainfall (mm)": rain_mm,
        "Solar Radiation (W/m²)": solar_wm2,
        "UV Index": uv_index,
    })
    
    # Add anomalies for QC testing
    if add_anomalies:
        # Add temperature spike
        spike_idx = np.random.choice(range(100, n-100), 5)
        df.loc[spike_idx, "Temperature (°F)"] += np.random.uniform(30, 50, len(spike_idx))
        
        # Add flatline (stuck sensor)
        flatline_start = np.random.choice(range(100, n-200))
        flatline_length = 50
        df.loc[flatline_start:flatline_start+flatline_length, "Relative Humidity (%)"] = 65.0
        
        # Add out-of-range value
        df.loc[np.random.choice(range(100, n-100)), "Relative Humidity (%)"] = 150.0
        
        # Add negative pressure (impossible)
        df.loc[np.random.choice(range(100, n-100)), "Pressure (mbar)"] = -10.0
    
    # Add gaps
    if add_gaps:
        gap_indices = np.random.choice(range(100, n-100), size=int(n * 0.02), replace=False)
        df.loc[gap_indices, df.columns[1:]] = np.nan
    
    return df


if __name__ == "__main__":
    # Generate full year of 10-minute data
    df = generate_sample_weather_data(
        start_date="2024-01-01",
        end_date="2024-12-31",
        freq="10min",
        add_gaps=True,
        add_anomalies=True,
        seed=42
    )
    
    # Save to CSV
    output_path = "sample_weather_2024.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} records")
    print(f"Saved to {output_path}")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nData summary:")
    print(df.describe())


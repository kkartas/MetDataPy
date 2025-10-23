# MetDataPy Performance Benchmarks

Performance benchmarks demonstrating MetDataPy's computational efficiency for meteorological data processing.

## Running Benchmarks

```bash
cd benchmarks
python benchmark_performance.py
```

## Benchmark Results

Tested on typical hardware with datasets ranging from 1,000 to 100,000 rows.

### Throughput (rows/second)

| Operation | Small (1k) | Medium (10k) | Large (52k) | XLarge (100k) |
|-----------|------------|--------------|-------------|---------------|
| **Quality Control** | 39,016 | 146,331 | 169,794 | 156,231 |
| **Derived Metrics** | 86,207 | 905,838 | 2,630,762 | 2,500,256 |
| **Resampling** | 158,821 | 1,994,913 | 5,818,688 | 4,117,270 |
| **Calendar Features** | 221,593 | 1,875,975 | 3,134,412 | 3,057,162 |
| **ML Preparation** | - | 538,207 | 1,199,155 | 1,533,443 |

### Real-World Performance

**1 year of 10-minute weather data (52,560 rows):**
- Complete pipeline: ~0.36 seconds
- Quality control: 310ms
- 4 derived metrics: 20ms
- Resample to hourly: 9ms
- Calendar features: 17ms

**100,000 rows (~2 years of 10-min data):**
- Complete pipeline: ~0.7 seconds
- Quality control: 640ms
- All operations scale linearly

## Performance Characteristics

### Strengths
- ✅ **Vectorized operations**: Heavy use of pandas/numpy for speed
- ✅ **Linear scaling**: Performance scales linearly with data size
- ✅ **Memory efficient**: In-place operations where possible
- ✅ **Fast derived metrics**: 2.5M+ rows/second for calculations

### Operations Breakdown

**Quality Control** (~170k rows/s)
- Range checks: O(n)
- Spike detection: O(n×w) with rolling window
- Flatline detection: O(n×w) with rolling variance
- Most time spent on rolling operations

**Derived Metrics** (~2.6M rows/s)
- Dew point: Vectorized Magnus formula
- VPD: Saturation vapor pressure calculation
- Heat index: Rothfusz regression
- Wind chill: North American formula
- All fully vectorized numpy operations

**Resampling** (~5.8M rows/s)
- Pandas native resampling (highly optimized)
- Aggregation rules per variable
- QC flag propagation via logical OR

**ML Preparation** (~1.2M rows/s)
- Lag feature creation: Multiple shift operations
- Target horizon generation
- Supervised table construction

## Typical Use Cases

### Use Case 1: Single Weather Station (1 year)
- **Data size:** 52,560 rows (10-min intervals)
- **Processing time:** <0.5 seconds
- **Operations:** Full pipeline (QC + derive + resample + ML prep)

### Use Case 2: Sensor Network (10 stations × 1 year)
- **Data size:** 525,600 rows
- **Processing time:** ~5 seconds
- **Throughput:** ~100k rows/second

### Use Case 3: Research Dataset (10 years)
- **Data size:** 525,600 rows  
- **Processing time:** ~5 seconds
- **Memory:** ~28 MB

## Optimization Notes

MetDataPy is designed for:
- ✅ **Small to medium datasets** (typical weather station data)
- ✅ **Interactive workflows** (Jupyter notebooks, exploratory analysis)
- ✅ **Production pipelines** (automated processing scripts)

For very large datasets (millions of rows, multiple stations), consider:
- Processing stations in parallel
- Using chunked processing for extremely large files
- Leveraging Dask for distributed computation (future work)

## Environment

Benchmarks run on:
- Python 3.11
- pandas 2.x
- numpy 2.x
- Consumer-grade hardware

Performance may vary based on:
- CPU speed
- Available RAM
- Pandas/NumPy versions
- Operating system

## Reproducing Benchmarks

```bash
# Install MetDataPy
pip install -e .

# Run benchmarks
cd benchmarks
python benchmark_performance.py

# Expected runtime: ~5-10 seconds
```

## Conclusion

MetDataPy provides **excellent performance** for typical meteorological data processing workflows:
- ✅ Sub-second processing for annual datasets
- ✅ Linear scaling with data size
- ✅ Production-ready for real-time and batch processing
- ✅ Memory efficient for multi-year datasets

The vectorized pandas/numpy operations ensure computational efficiency suitable for both research and operational applications.


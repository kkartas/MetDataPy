---
title: 'MetDataPy: A Source-Agnostic Toolkit for Meteorological Time-Series Data Preparation and Quality Control'
tags:
  - Python
  - meteorology
  - time series
  - quality control
  - machine learning
  - data preprocessing
authors:
  - name: Kyriakos Kartas
    orcid: 0009-0001-6477-4676
    affiliation: 1
affiliations:
  - name: Independent Researcher, Greece
    index: 1
date: 18 October 2025
bibliography: paper.bib
---

# Summary

MetDataPy is a Python package designed to streamline the ingestion, quality control, and preparation of meteorological time-series data for machine learning applications. Weather data from diverse sources—such as weather stations, citizen science networks, and IoT sensors—typically arrive in heterogeneous formats with varying units, inconsistent timestamps, and quality issues. MetDataPy addresses these challenges by providing a unified canonical schema, automated column mapping with source detection, comprehensive quality control algorithms, and reproducible ML-ready data pipelines. The package enables researchers and practitioners to transform raw meteorological observations into clean, well-documented datasets suitable for forecasting, climate analysis, and agricultural modeling. The software is freely available under the MIT license at https://github.com/kkartas/MetDataPy with comprehensive documentation at https://metdatapy.readthedocs.io/.

# Installation

MetDataPy can be installed via pip from the Python Package Index (PyPI):

```bash
pip install metdatapy
```

For optional features including NetCDF export and advanced ML functionality:

```bash
pip install metdatapy[ml,extras]
```

The package requires Python 3.9 or later and depends on core scientific Python libraries including pandas (≥2.0), NumPy (≥1.23), and PyYAML (≥6.0). Development installation from source is available via:

```bash
git clone https://github.com/kkartas/MetDataPy
cd MetDataPy
pip install -e .
```

# Statement of Need

Machine learning applications in atmospheric sciences, agriculture, and renewable energy increasingly rely on high-quality meteorological time-series data [@rasp2020weatherbench; @schultz2021can]. However, preparing such data remains time-consuming and error-prone due to several challenges: (1) heterogeneous data formats across providers (NOAA, Weathercloud, custom stations); (2) unit inconsistencies (Fahrenheit vs. Celsius, mph vs. m/s); (3) temporal issues including timezone handling, daylight saving transitions, and irregular sampling; (4) quality problems such as sensor drift, outliers, and missing values; and (5) ML-specific requirements like time-safe data splitting and feature scaling. A typical workflow might involve manually mapping dozens of column names, writing custom unit conversion functions, implementing ad-hoc quality checks, and carefully managing train-test splits to prevent temporal leakage—processes that are both error-prone and difficult to reproduce across research groups.

Existing tools address subsets of these challenges. `pandas` [@mckinney2010data] provides general-purpose time-series manipulation but lacks meteorology-specific quality control and domain knowledge. MetPy [@may2022metpy] offers comprehensive meteorological calculations but focuses primarily on thermodynamic computations and vertical profile analysis rather than data ingestion and ML preparation. `xarray` [@hoyer2017xarray] excels at multidimensional climate data but requires users to implement quality control manually and does not provide ML-oriented preprocessing. `tsfresh` [@christ2018time] automates time-series feature extraction but does not address domain-specific meteorological derived variables, quality flagging protocols, or the unique challenges of weather data (e.g., wind direction circularity, accumulated precipitation rollovers).

MetDataPy fills this gap by providing an end-to-end workflow specifically designed for meteorological time-series data preparation. Its key contributions include:

1. **Source-agnostic ingestion**: Automatic column detection using heuristics (regex patterns, unit hints, statistical plausibility) with confidence scoring, enabling seamless integration of data from diverse providers without manual schema mapping. The detector assigns confidence scores based on name matching, unit inference, and statistical plausibility checks against meteorological bounds, with an interactive wizard for refinement.

2. **Comprehensive quality control**: Meteorological QC algorithms including range checks against climatological bounds, spike detection using rolling Median Absolute Deviation [@leys2013detecting] which is more robust than standard deviation, flatline detection via rolling variance to identify stuck sensors, and cross-variable consistency checks exploiting physical relationships (e.g., dew point ≤ temperature, wind direction undefined when wind speed ≈ 0). All checks produce boolean flags preserving provenance without destructive deletion. QC parameters are configurable via YAML, with reports providing statistical summaries by variable and flag type.

3. **Derived meteorological metrics**: Scientifically validated calculations of dew point using the Magnus-Tetens approximation [@lawrence2005relationship], vapor pressure deficit following FAO-56 guidelines [@allen1998crop], heat index using the Rothfusz regression [@rothfusz1990heat] with Steadman adjustments, and wind chill following the 2001 North American wind chill equivalent temperature chart [@osczevski2005new]. All formulations include complete references to peer-reviewed literature and specify valid ranges and assumptions. These derived variables are crucial for agricultural decision support systems, outdoor worker safety applications, and energy demand forecasting.

4. **ML-ready preparation**: Time-safe data splitting preventing temporal leakage, supervised learning table generation with configurable lags and forecast horizons, and reproducible scaling with parameter serialization. The package supports standard, min-max, and robust scaling with parameters serialized to JSON for exact reproducibility. Calendar features (hour, day-of-week, month, cyclical encodings) are automatically generated, and external covariates can be aligned by timestamp.

5. **Reproducibility infrastructure**: CF-compliant NetCDF export [@eaton2020netcdf] following CF-1.8 conventions with comprehensive metadata and proper QC flag handling. Manifest generation tracks all pipeline steps with timestamps, software versions, parameters, and a deterministic pipeline hash. Pydantic-validated schemas ensure type safety and enable manifest comparison for reproducibility verification. Command-line tools (`mdp manifest validate`, `show`, `compare`) facilitate auditing and debugging.

# Implementation and Design

The package is structured around a core `WeatherSet` class providing a fluent API for chaining operations while maintaining data provenance. The canonical schema defines nine core meteorological variables with standardized names and SI-derived units. Timezone handling ensures all timestamps are converted to UTC, eliminating ambiguity from daylight saving transitions. Special handling detects and corrects accumulated rainfall sensor rollovers. Resampling operations intelligently aggregate variables (mean for intensive quantities, sum for extensive) while conservatively propagating quality flags using logical OR. The implementation emphasizes computational efficiency through vectorized pandas and NumPy operations, processing typical annual weather station datasets (52,000 rows at 10-minute resolution) in under 500 milliseconds on consumer hardware.

The command-line interface (`mdp`) provides composable commands for detection, ingestion, quality control, and export, enabling integration into automated pipelines. The Python API allows fine-grained control for Jupyter notebooks and custom scripts. Comprehensive documentation includes API references, tutorials, and a publication-quality Jupyter notebook with visualizations.

# Use Cases and Applications

MetDataPy supports diverse applications across atmospheric and agricultural sciences. In **precision agriculture**, it processes weather station data to compute growing degree days and evapotranspiration for irrigation scheduling. For **renewable energy forecasting**, it prepares historical weather data with appropriate lags and derived features for training solar and wind power prediction models. In **urban climate studies**, it harmonizes data from heterogeneous sensor networks, applying consistent quality control before spatial interpolation. **Climate model validation** workflows use MetDataPy to prepare observational benchmarks with uncertainty quantification via QC flags, enabling comparisons with model outputs in CF-compliant NetCDF format.

The package prioritizes scientific correctness, reproducibility, and ease of use, lowering the barrier for researchers to adopt best practices. By providing well-tested implementations with complete literature references, MetDataPy reduces duplication of effort and potential errors in custom preprocessing code.

# Acknowledgements

The development of MetDataPy was inspired by challenges encountered in real-world meteorological data processing workflows and benefited from the extensive Python scientific computing ecosystem, including NumPy [@harris2020array], pandas [@mckinney2010data], and scikit-learn [@pedregosa2011scikit]. The project welcomes community contributions following the guidelines in CONTRIBUTING.md, and adheres to the Contributor Covenant Code of Conduct to foster an inclusive and collaborative development environment.

# References


# Scientific References

This page lists all scientific literature referenced in MetDataPy's implementations.

## Derived Meteorological Metrics

### Dew Point Temperature

**Magnus-Tetens Formula**

The dew point calculation uses the improved Magnus form approximation:

- **Alduchov, O. A., & Eskridge, R. E. (1996)**. Improved Magnus form approximation of saturation vapor pressure. *Journal of Applied Meteorology*, 35(4), 601-609.  
  DOI: [10.1175/1520-0450(1996)035<0601:IMFAOS>2.0.CO;2](https://doi.org/10.1175/1520-0450(1996)035<0601:IMFAOS>2.0.CO;2)

- **Lawrence, M. G. (2005)**. The relationship between relative humidity and the dewpoint temperature in moist air: A simple conversion and applications. *Bulletin of the American Meteorological Society*, 86(2), 225-233.  
  DOI: [10.1175/BAMS-86-2-225](https://doi.org/10.1175/BAMS-86-2-225)

### Saturation Vapor Pressure

**Tetens Formula**

- **Tetens, O. (1930)**. Über einige meteorologische Begriffe. *Zeitschrift für Geophysik*, 6, 297-309.

- **Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998)**. Crop evapotranspiration - Guidelines for computing crop water requirements. *FAO Irrigation and drainage paper 56*. Food and Agriculture Organization of the United Nations, Rome.  
  [Available online](http://www.fao.org/3/x0490e/x0490e00.htm)

### Vapor Pressure Deficit (VPD)

- **Allen, R. G., et al. (1998)**. Crop evapotranspiration. *FAO Irrigation and drainage paper 56*.

- **Grossiord, C., et al. (2020)**. Plant responses to rising vapor pressure deficit. *New Phytologist*, 226(6), 1550-1566.  
  DOI: [10.1111/nph.16485](https://doi.org/10.1111/nph.16485)

### Heat Index

**Rothfusz Regression & Steadman Model**

- **Rothfusz, L. P. (1990)**. The heat index equation (or, more than you ever wanted to know about heat index). *National Weather Service Technical Attachment SR 90-23*.  
  [Available online](https://www.weather.gov/media/ffc/ta_htindx.PDF)

- **Steadman, R. G. (1979)**. The assessment of sultriness. Part I: A temperature-humidity index based on human physiology and clothing science. *Journal of Applied Meteorology*, 18(7), 861-873.  
  DOI: [10.1175/1520-0450(1979)018<0861:TAOSPI>2.0.CO;2](https://doi.org/10.1175/1520-0450(1979)018<0861:TAOSPI>2.0.CO;2)

- **Anderson, G. B., et al. (2013)**. Heat-related emergency hospitalizations for respiratory diseases in the Medicare population. *American Journal of Respiratory and Critical Care Medicine*, 187(10), 1098-1103.  
  DOI: [10.1164/rccm.201211-1969OC](https://doi.org/10.1164/rccm.201211-1969OC)

### Wind Chill

**North American Wind Chill Formula (2001)**

- **Osczevski, R., & Bluestein, M. (2005)**. The new wind chill equivalent temperature chart. *Bulletin of the American Meteorological Society*, 86(10), 1453-1458.  
  DOI: [10.1175/BAMS-86-10-1453](https://doi.org/10.1175/BAMS-86-10-1453)

- **Tikuisis, P., & Osczevski, R. J. (2003)**. Facial cooling during cold air exposure. *Bulletin of the American Meteorological Society*, 84(7), 927-934.  
  DOI: [10.1175/BAMS-84-7-927](https://doi.org/10.1175/BAMS-84-7-927)

- **Shitzer, A., & de Dear, R. (2006)**. Inconsistencies in the "New" windchill chart at low wind speeds. *Journal of Applied Meteorology and Climatology*, 45(5), 787-790.  
  DOI: [10.1175/JAM2360.1](https://doi.org/10.1175/JAM2360.1)

## Quality Control Methods

### Spike Detection

**Rolling Median Absolute Deviation (MAD)**

- **Leys, C., et al. (2013)**. Detecting outliers: Do not use standard deviation around the mean, use absolute deviation around the median. *Journal of Experimental Social Psychology*, 49(4), 764-766.  
  DOI: [10.1016/j.jesp.2013.03.013](https://doi.org/10.1016/j.jesp.2013.03.013)

### Flatline Detection

**Rolling Variance Method**

- **Shaadan, N., et al. (2015)**. Anomaly detection in univariate time-series: A survey on the state-of-the-art. *Journal of Engineering Science and Technology*, 10(Special Issue), 1-13.

## Data Standards

### CF Conventions

- **Eaton, B., et al. (2020)**. NetCDF Climate and Forecast (CF) Metadata Conventions, Version 1.8.  
  [Available online](http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html)

### FAIR Principles

- **Wilkinson, M. D., et al. (2016)**. The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, 3, 160018.  
  DOI: [10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18)

## Related Software

### Comparison Tools

- **MetPy**: May, R. M., et al. (2022). MetPy: A Python Package for Meteorological Data. *Unidata*.  
  DOI: [10.5065/D6WW7G29](https://doi.org/10.5065/D6WW7G29)

- **xarray**: Hoyer, S., & Hamman, J. (2017). xarray: N-D labeled arrays and datasets in Python. *Journal of Open Research Software*, 5(1), 10.  
  DOI: [10.5334/jors.148](https://doi.org/10.5334/jors.148)

- **pandas**: McKinney, W. (2010). Data structures for statistical computing in Python. *Proceedings of the 9th Python in Science Conference*, 56-61.  
  DOI: [10.25080/Majora-92bf1922-00a](https://doi.org/10.25080/Majora-92bf1922-00a)

## Citing MetDataPy

If you use MetDataPy in your research, please cite:

```bibtex
@software{metdatapy2025,
  title = {MetDataPy: A Source-Agnostic Toolkit for Meteorological Time-Series Data},
  author = {Kartas, Kyriakos},
  year = {2025},
  url = {https://github.com/kkartas/MetDataPy},
  version = {0.0.1}
}
```

See `CITATION.cff` for machine-readable citation metadata.

## Additional Resources

### Meteorological Standards

- **World Meteorological Organization (WMO)**. Guide to Meteorological Instruments and Methods of Observation (WMO-No. 8), 2018 edition.  
  [Available online](https://library.wmo.int/index.php?lvl=notice_display&id=12407)

### Time Series Analysis

- **Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M. (2015)**. Time Series Analysis: Forecasting and Control (5th ed.). John Wiley & Sons.

### Machine Learning for Weather

- **Reichstein, M., et al. (2019)**. Deep learning and process understanding for data-driven Earth system science. *Nature*, 566(7743), 195-204.  
  DOI: [10.1038/s41586-019-0912-1](https://doi.org/10.1038/s41586-019-0912-1)

- **Schultz, M. G., et al. (2021)**. Can deep learning beat numerical weather prediction? *Philosophical Transactions of the Royal Society A*, 379(2194), 20200097.  
  DOI: [10.1098/rsta.2020.0097](https://doi.org/10.1098/rsta.2020.0097)

## Contributing References

If you implement new meteorological formulas or QC methods, please:

1. Add citations to the function docstring
2. Update this references page
3. Include DOI links when available
4. Follow the NumPy docstring format

See `CONTRIBUTING.md` for details.


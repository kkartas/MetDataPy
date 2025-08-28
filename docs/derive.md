# Derived Metrics

## Dew Point (Magnus)

Let A=17.62, B=243.12 °C:
\[ \gamma(T, RH) = \ln(RH/100) + \frac{A T}{B + T} \]
\[ T_d = \frac{B\,\gamma}{A - \gamma} \]

## Vapor Pressure Deficit (VPD)

Using Tetens equation for saturation vapor pressure:
\[ e_s(T) = 0.6108 \exp\left(\frac{17.27 T}{T + 237.3}\right) \]
\[ e_a = e_s(T) \cdot RH/100 \]
\[ \mathrm{VPD} = e_s - e_a \quad (\mathrm{kPa}) \]

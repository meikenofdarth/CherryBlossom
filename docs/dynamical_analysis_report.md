# Mathematical Variables & Results (Kyoto Cherry Blossom Phenology)

This document serves as a straightforward mathematical cheat sheet for the variables calculated from the Yasuyuki Aono dataset (`kyoto2010flower.txt`) and temperature reconstructions. 

---

### 1. Fundamental Variables
*   **$n$ (State Variable):** The Day of the Year (DOY) of full bloom.
*   **$t$ (Time):** The year of observation.
*   **$T$ (Forcing Variable):** The reconstructed March temperature (in °C).
*   **$dn/dt$ (Velocity):** The rate of change of the bloom date, approximated using the forward difference: $(n_{t+1} - n_t) / (t_{t+1} - t_t)$.

---

### 2. Baseline Dynamical Parameters ($dn/dt = -k \cdot n + c$)
*   **$n_{eq}$ (Natural Equilibrium)**
    *   *Calculation:* Derived from the regression intercept ($c$) and slope ($-k$) where $n_{eq} = c / k$.
    *   *Significance:* The theoretical "resting state" or baseline average bloom date if weather noise is removed.
    *   *Value (812 AD - 1850 AD):* **105.22**
    *   *Value (1851 AD - Present):* **102.05**
*   **$k$ (Restoring Force)**
    *   *Calculation:* The negative slope of the linear regression between $dn/dt$ and $n$.
    *   *Significance:* Measures the elasticity of the system (how strongly it pulls back to equilibrium after a disturbance).
    *   *Value (812 AD - 1850 AD):* **0.7663**
    *   *Value (1851 AD - Present):* **0.6131**
*   **$\sigma$ (Natural Volatility)**
    *   *Calculation:* The standard deviation of the residuals from the $dn/dt$ regression.
    *   *Significance:* The magnitude of average year-to-year variance caused by random weather noise.
    *   *Value (812 AD - 1850 AD):* **5.98** days/year
    *   *Value (1851 AD - Present):* **5.24** days/year

---
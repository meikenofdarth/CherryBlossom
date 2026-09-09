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

### 3. Temperature Forcing / ARX Model ($n_t = a \cdot n_{t-1} + b \cdot T_t + c$)
*   **$a$ (Autoregressive Coefficient)**
    *   *Calculation:* The coefficient for the previous year's bloom date ($n_{t-1}$) in a multiple linear regression.
    *   *Significance:* Quantifies the biological "memory" of the system from year to year.
    *   *Value:* **-0.0027** ($\approx 0$, meaning the system is memoryless).
*   **$\beta$ (Temperature Sensitivity)**
    *   *Calculation:* $\beta = b / (1 - a)$. Derived from the direct temperature coefficient ($b$) and the autoregressive term ($a$).
    *   *Significance:* The exact shift in the equilibrium bloom date for every $1^\circ\text{C}$ increase in March temperature.
    *   *Value:* **-3.46** days / $^\circ\text{C}$

---

### 4. Critical Slowing Down (Pre-Industrial: 1000 AD - 1850 AD)
*   **Kendall-$\tau$ (Rolling Variance)**
    *   *Calculation:* The rank correlation between time ($t$) and a 50-year rolling variance of the detrended residuals.
    *   *Significance:* A positive trend indicates increasing variance, a mathematical early warning signal of a system approaching a tipping point.
    *   *Value:* **0.3721** (p-value: $4.14 \times 10^{-42}$)
*   **Kendall-$\tau$ (Rolling AR1)**
    *   *Calculation:* The rank correlation between time ($t$) and a 50-year rolling Lag-1 Autocorrelation.
    *   *Significance:* Used alongside variance to test for critical slowing down.
    *   *Value:* **-0.5184** (p-value: $4.88 \times 10^{-80}$)

---

### 5. Takens' Embedding & Chaos Metrics
*   **$\tau$ (Optimal Time Delay)**
    *   *Calculation:* The first time lag where the autocorrelation function drops below $1/e$.
    *   *Significance:* Used to space out data points for phase space reconstruction without them being overly correlated.
    *   *Value:* **2 years**
*   **$D_2$ (Correlation Dimension)**
    *   *Calculation:* Calculated using the Grassberger-Procaccia algorithm on the 1D time series.
    *   *Significance:* The integer ceiling of $D_2$ dictates the minimum number of independent dynamic variables governing the Kyoto climate attractor.
    *   *Value:* **0.3028** (Ceiling = 1 variable)
*   **$\lambda$ (Maximal Lyapunov Exponent)**
    *   *Calculation:* Calculated using the Rosenstein algorithm tracking the exponential divergence of nearby trajectories.
    *   *Significance:* $\lambda > 0$ implies deterministic chaos (sensitive dependence on initial conditions).
    *   *Value:* **0.0015** (Barely chaotic; highly stable system)

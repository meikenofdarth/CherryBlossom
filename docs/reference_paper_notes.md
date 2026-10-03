# Reference Paper and Its Use in This Project

Reference: Sunny, Balakrishnan and Kurths, **Predicting climatic tipping points**, *Chaos* 33, 021101 (2023), doi: 10.1063/5.0135266. The supplied PDF is [jb_etal_chaos_tippingpts.pdf](jb_etal_chaos_tippingpts.pdf).

## What The Paper Does

The paper uses a time-dependent generalized logistic model for fossil-fuel CO2 emissions:

$$
\frac{dN}{dt} = A_0(t) + r(t)N\left(1-\frac{N}{K(t)}\right)
$$

The model allows parameters and equilibria to change over time. It studies two ideas:

- a system may fail to follow a moving stable equilibrium when the parameter changes too quickly;
- a threshold crossing can move the system into a different dynamical regime.

The paper estimates measurable parameters from data, identifies transitions and discusses fixed points, basins of attraction and rate-induced tipping.

## What Transfers To Cherry Blossom Data

The useful ideas are:

1. Treat bloom timing as a dynamical observable, not only as a regression outcome.
2. Separate the state variable from the external forcing. For us, the state could be bloom DOY or an anomaly, while temperature is an external driver.
3. Ask whether the equilibrium or trend changes over time rather than assuming one fixed relationship.
4. Use phase-space plots to inspect state and rate together.
5. If a time-dependent model is attempted, report the parameter meaning and the conditions under which a regime shift would occur.

A possible simple state-forcing form is:

$$
\frac{dD_s}{dt} = -k_s\left[D_s - D^*_s(T,t)\right] + \epsilon_s(t)
$$

where:

- $D_s$ is bloom DOY for station or species $s$;
- $k_s$ is a relaxation rate;
- $D^*_s(T,t)$ is a temperature-dependent moving equilibrium;
- $\epsilon_s(t)$ contains weather and observation noise.

A simple moving equilibrium could be:

$$
D^*_s(T,t) = a_s - b_sT_s(t) + c_st
$$

This connects the nonlinear-dynamics framing to the already observed temperature sensitivity without inventing a complicated model.

## What Does Not Transfer Directly

The paper studies a growth process with a clear state variable, time-varying logistic parameters and regime-transition mechanisms. Cherry bloom dates are annual observations, not a continuous CO2-growth process. Our data do not currently demonstrate:

- multiple stable equilibria;
- a basin boundary;
- a bifurcation;
- a rate-induced tipping point;
- an irreversible regime shift.

The station restoring-force experiment was weak: Wakkanai, Kagoshima, Matsumoto and Kyoto all had raw annual phase-space $R^2$ values below 0.003, and the confidence intervals for $k$ included zero. Therefore, we should not claim that cherry flowering has a tipping point based on the current results.

## Appropriate Use In The Final Project

Use the paper to motivate the language of:

- state variable;
- external forcing;
- moving equilibrium;
- relaxation rate;
- phase space;
- regime change as a hypothesis to test.

Do not copy its logistic or tipping-point claims into the cherry project without evidence. The safest next model is a temperature-forced relaxation model, compared against the existing station regressions and evaluated on held-out years.

## Suggested Minimal Next Model

For each station with adequate weather coverage, compare these models:

### Baseline

$$
D_{s,t} = a_s + b_s T_{s,t} + e_{s,t}
$$

### Moving-equilibrium relaxation model

$$
\frac{dD_{s,t}}{dt} = -k_sD_{s,t} + c_s + q_sT_{s,t} + e_{s,t}
$$

Estimate the derivative with the actual year spacing, as already done for the phase-space diagnostic. Keep this as a simple exploratory dynamics model, not a claim of tipping.

### Regime-change check

Compare the fitted relationship before and after approximately 1850 for Kyoto, or before and after a modern split for station data. A regime-change claim requires:

- a clear improvement over one-regime models;
- stable results across reasonable split dates;
- held-out predictive improvement;
- uncertainty intervals that do not merely reflect noisy derivative estimation.

## Current Project Position

The strongest established result remains statistical: almost all retained stations show earlier full bloom, with a median near one day earlier per decade and stability across common windows. The strongest mechanistic result is the station-level temperature association. The physical degree-day model is a simple secondary comparison. The reference paper now supports a careful dynamical interpretation, but it does not yet provide evidence for a climatic tipping point in the cherry data.

The first moving-equilibrium implementation has now been tested. It uses consecutive-year full-bloom DOY, February-March temperature and year, with training through 1990 and testing after 1990. All 19 weather stations fit. The median held-out RMSE is **4.4132 days**, compared with **4.5232 days** for a same-split station-specific temperature baseline, and 10 of 19 stations improve. Eighteen of 19 relaxation confidence intervals include zero. This makes it a useful exploratory bridge to the paper, not the project's final equation or evidence of tipping.

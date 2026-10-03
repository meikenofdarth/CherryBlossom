# Next Chat Handoff

## Project Goal

Study cherry blossom first bloom, full bloom and duration in Japan, then form the simplest defensible temperature-based physical-response model. Do not claim tipping points, bifurcations or an exact biological law.

## Current Adopted Model

The adopted model is the empirical Kyoto JMA temperature response:

$$
D_{Kyoto} = 119.55 - 2.878T_{March}
$$

Using 72 Kyoto JMA station-weather years:

- $R^2 = 0.720$
- slope 95% CI: **[−3.305, −2.450] days/$^\circ$C**
- $D$ is full-bloom DOY
- $T_{March}$ is JMA March mean temperature

This is an empirical physical-response model, not a complete plant-process equation.

## Strong Findings

- 102 JMA phenology stations, 1953-2025.
- Main comparison excludes Taiwan cherry, Kurile cherry and Kutchan.
- 73 Not stated stations in 1961-2010 have at least 40 valid years.
- 98.6% show earlier full bloom.
- The negative full-bloom result remains approximately 98% across three common windows.
- Official JMA coordinates are used for geographic analyses.
- Official JMA daily weather was collected for 20 stations, 1953-2024.
- Daily JMA rows: **85,216**.
- Joined eligible station-weather rows: **1,355**.
- Nara February/March 1953 is a documented JMA source gap.
- JMA duration-temperature examples: Kyoto +1.18, Fukuoka +1.37, Kagoshima +1.10, Aomori −0.21, Akita −0.10, Wakkanai −0.28 days/$^\circ$C.

## Models Tested But Not Adopted

### Fixed degree-day model

- Base temperature: $0^\circ$C
- Start: February 1
- Threshold: 400 degree-days
- JMA out-of-sample RMSE: **7.2938 days**
- Matched linear JMA model out-of-sample RMSE: **4.0473 days**
- Keep as a transparent rejected baseline.

### Autonomous restoring force

$$
\frac{dD}{dt} = -kD + c
$$

Selected station $R^2$ values were below 0.003. Treat as diagnostic only.

### Moving equilibrium

$$
D_t = a + \phi D_{t-1} + \beta T_t + \gamma t + e_t
$$

JMA results:

- moving-equilibrium median test RMSE: **4.3176 days**
- matched baseline median test RMSE: **4.0455 days**
- improvement at 9 of 19 stations
- all 19 relaxation confidence intervals include zero

Treat as exploratory only. No tipping-point claim.

## Limit-Cycle Follow-up (Exploratory, 2026-10-03)

Four representative stations (Kyoto, Wakkanai, Kagoshima and Osaka) were audited for coverage, smoothing sensitivity, detrended period peaks, recurrence/closure, and held-out model performance. The smooth phase paths do not consistently close; the period screen does not establish recurrence; and a training-selected periodic term beat the temperature-only model at only 1 of 8 station/bloom-stage pairs. Keep these results exploratory and do not claim an autonomous limit cycle.

Key outputs:

- `data/advanced_dynamics_station_audit.csv`
- `data/phase_space_smoothing_sensitivity.csv`
- `data/phase_space_oscillation_screen.csv`
- `data/phase_space_recurrence_audit.csv`
- `data/recurrence_model_holdout_scores.csv`
- `data/recurrence_model_holdout_predictions.csv`
- `docs/research_log.md` entries H27-H30

## Key Files

- Overview: [project_summary.md](project_summary.md)
- Research history: [research_log.md](research_log.md)
- Architecture: [research_architecture_plan.md](research_architecture_plan.md)
- Current state: [state.md](state.md)
- Reference paper notes: [reference_paper_notes.md](reference_paper_notes.md)
- Canonical phenology: `data/station_year_phenology.csv`
- Canonical JMA weather join: `data/station_year_weather_jma.csv`
- JMA daily data: `data/jma_daily_observed_streaming.csv`
- JMA weather validation: `data/jma_weather_validation.txt`
- Kyoto equation results: `data/kyoto_jma_degree_day_results.csv`
- JMA station sensitivity: `data/station_temperature_sensitivity_jma.csv`
- 73-station duration trend vs latitude: `data/station_duration_slope_latitude_jma.csv`
- 20-station duration-temperature slope vs latitude: `data/station_duration_temperature_slope_latitude_jma.csv`
- JMA moving equilibrium: `data/station_moving_equilibrium_jma.csv`

## Main Commands

```bash
python3 scripts/build_station_year_table.py
python3 scripts/build_jma_weather_table.py
WEATHER_FILE=data/station_year_weather_jma.csv python3 scripts/station_physical_analysis.py
WEATHER_FILE=data/station_year_weather_jma.csv python3 scripts/jma_temperature_sensitivity.py
WEATHER_FILE=data/station_year_weather_jma.csv python3 scripts/station_moving_equilibrium.py
python3 scripts/jma_degree_day_model.py
python3 -m py_compile scripts/*.py
```

## Remaining Work

1. Verify the final numbers and remove stale Open-Meteo wording from any presentation material.
2. Decide whether the Kyoto equation should use March temperature or Feb-March temperature; March is the adopted form above.
3. Confirm the `Not stated = Yoshino` assumption from source documentation, or label it explicitly as an assumption.
4. Check whether recent Aono Kyoto observations overlap the JMA Kyoto series.
5. Prepare final figures and presentation.
6. Keep degree-day, restoring-force and moving-equilibrium results as exploratory comparisons.
7. Do not add chilling models, grid searches, hierarchical models or tipping-point claims in this project unless the scope is deliberately reopened.
8. The four-station limit-cycle follow-up did not validate a cycle or improve held-out predictions with a periodic term; any further work should either expand these prespecified checks to the eligible network or prepare the current cautious result for presentation.

## Important Warnings

- Do not use the old mixed reconstructed/observed Kyoto temperature plots.
- Do not treat 102 stations as independent samples.
- Do not call the empirical equation a complete biological law.
- Do not claim that the reference paper proves tipping in the cherry data.
- Open-Meteo outputs are comparison data; JMA observations are preferred.

# Research Architecture and Exploration Plan

## Purpose

The project should move from descriptive trend analysis toward a defensible biological model of cherry blossom timing. The target is not simply a formula that fits the existing dates. The target is a model that:

1. uses independent temperature information,
2. represents plausible plant processes,
3. works across stations and years,
4. can be tested on years not used for calibration,
5. reports uncertainty and regional differences clearly.

The central modelling question is:

> Can first bloom, full bloom and bloom duration be explained by accumulated heat, winter chilling, geography and long-term change?

The current project already provides a strong descriptive foundation. The plan below describes how to expand it without mixing exploratory results into the final claims.

The supplied nonlinear-dynamics reference is [reference_paper_notes.md](reference_paper_notes.md). Its concepts of moving equilibria and parameter-rate effects are useful framing, but tipping-point claims remain out of scope unless the data demonstrate them.

## Current Starting Point

### Strong evidence already available

- Kyoto has a long Aono record from approximately 812 AD to the present.
- Kyoto has 118 years with observed March temperatures.
- Kyoto bloom timing is associated with March temperature at approximately **−2.99 days per degree Celsius**, with $R^2 = 0.6623$.
- Kyoto has a strong post-1850 advance of approximately **−7.53 days per century**.
- The JMA station network shows earlier full bloom at nearly all retained stations.
- The earlier-bloom result survives several common windows.
- Latitude is related to mean bloom date and to the direction of duration change.
- Eight stations currently have February and March temperature data.
- The first 400-degree thermal-sum model is plausible but has RMSE **4.84 days**, worse than the simple linear comparison at **3.24 days**.

### Current limitations

- Temperature data cover only eight stations.
- The temperature data are from Open-Meteo, while the bloom observations are from JMA/Kaggle.
- The physical model uses one arbitrary threshold, one starting date and a zero-degree base temperature.
- Chilling requirements are not yet represented.
- The station observations are spatially correlated.
- The main species assignment `Not stated = Yoshino` remains a documented assumption.
- The existing station analysis is mostly one-station-at-a-time regression rather than a joint model.

## Proposed Project Architecture

### Layer 1: Source data

Keep raw data unchanged and record source metadata.

- Aono Kyoto bloom series: `data/kyoto2010flower.txt`
- Aono temperature series: `data/kyoto2010temp.txt`
- JMA/Kaggle first bloom: `sakura_first_bloom_dates.csv`
- JMA/Kaggle full bloom: `sakura_full_bloom_dates.csv`
- Official JMA coordinates: `station_coords_template.csv`
- Station temperature data: `jma_temperatures.csv`
- Daily temperature data for physical modelling

Every downloaded temperature dataset should record source, coordinates, date range, variable, units and retrieval date.

### Layer 2: Canonical cleaned tables

Create one canonical long-format table for each analysis rather than repeating date parsing in many scripts.

#### Station-year phenology table

One row per station and year, with:

- station name
- year
- species label and species-confidence flag
- first bloom date
- full bloom date
- normalized first-bloom DOY
- normalized full-bloom DOY
- actual duration in days
- observation status
- first and last valid year indicators
- coordinate and region metadata

#### Kyoto table

One row per year, with:

- Aono bloom DOY
- temperature value
- temperature source: observed or reconstructed
- source-overlap flag
- historical period label

#### Station-weather table

One row per station and year, with:

- February mean temperature
- March mean temperature
- February-March mean
- daily or weekly heat sums
- chilling metrics
- missing-data counts
- temperature source and station coordinates

All downstream models should read these canonical tables.

### Layer 3: Validation and quality gates

Before modelling, run automated checks:

- dates parse successfully;
- first bloom is not after full bloom, except for explicitly handled cross-year species;
- Taiwan cherry uses season-relative dates;
- leap-year normalization is consistent;
- no duplicate station-year rows;
- temperature units and date ranges are valid;
- coordinates are complete and traceable to JMA;
- each model reports its sample size and station count;
- training and test years are separated before model fitting.

A model should not produce a final plot if these checks fail.

### Layer 4: Descriptive baseline models

Retain simple baselines so every physical model has a fair comparison.

1. Station-specific linear trend:
   $$
   D_{s,t} = a_s + b_s t + e_{s,t}
   $$
2. Temperature-only regression:
   $$
   D_{s,t} = a_s + b_s T_{s,t} + e_{s,t}
   $$
3. Temperature plus year:
   $$
   D_{s,t} = a_s + b_s T_{s,t} + c_s t + e_{s,t}
   $$
4. Regional or hierarchical version with shared effects.

Here $D$ is bloom DOY, $s$ is station and $t$ is year.

These baselines establish how much improvement a physical model actually provides.

## Physical Modelling Programme

### Stage A: Calibrate a degree-day model

Start with the simplest process model:

$$
G_{s,t}(d) = \sum_{i=d_0}^{d} \max(T_{s,t,i} - T_{base}, 0)
$$

Bloom is predicted on the first day $d$ for which:

$$
G_{s,t}(d) \geq H_s
$$

where:

- $d_0$ is the accumulation start date,
- $T_{base}$ is the base temperature,
- $H_s$ is the heat requirement.

Do not assume that 400 degree-days is universal. Test a grid such as:

- start date: January 1, January 15, February 1, February 15;
- base temperature: 0, 2.5, 4, 5 and 7 degrees Celsius;
- heat requirement: 200 through 800 degree-days;
- target: first bloom and full bloom separately.

For each combination, calculate out-of-sample RMSE and mean error. Select parameters using training years only, then evaluate once on held-out years.

Fit separate parameters for each species group if the data support it. At minimum, compare Yoshino and Sargent. Taiwan cherry should be modelled separately because its season crosses the calendar year and its thermal response may differ.

### Stage B: Add winter chilling

Heat accumulation alone may fail because flowering usually requires both chilling and forcing.

A simple two-stage model is:

1. chilling requirement is fulfilled when winter temperatures provide enough cold exposure;
2. heat accumulation begins or becomes effective after chilling is fulfilled.

Candidate chilling summaries:

- number of days below 7 degrees Celsius;
- number of hours below a base temperature;
- mean December-January temperature;
- Utah or Dynamic Chilling Portions model if hourly data are available.

Test whether adding chilling reduces systematic errors in cold northern stations and improves the duration analysis.

### Stage C: Model first bloom and full bloom jointly

First bloom and full bloom are not independent outcomes. Model them together through a latent flowering process or through separate thresholds:

$$
D^{first}_{s,t} = \text{first day } G_{s,t}(d) \geq H^{first}_s
$$

$$
D^{full}_{s,t} = \text{first day } G_{s,t}(d) \geq H^{full}_s
$$

with:

$$
H^{full}_s > H^{first}_s
$$

Then duration is generated by the difference between the two threshold-crossing dates rather than fitted as an unrelated response.

This directly connects the physical equation to the observed duration question.

### Stage D: Explain regional differences

Add station-level predictors:

- latitude
- longitude
- elevation
- coastal or inland classification
- winter chilling
- February and March temperatures
- station observation period
- species group

Use partial pooling so stations can have individual behavior while sharing information:

$$
H_s = H_0 + u_{species(s)} + u_{region(s)} + u_s
$$

A simpler intermediate model is a mixed-effects regression with station and year effects. The important test is whether latitude still predicts duration after temperature and chilling are included.

### Stage E: Evaluate dynamical equations

The original assignment asks about $x_1$, $x_2$, and their rates of change. We should connect that request to the biological model rather than fit arbitrary curves to noisy derivatives.

Useful state variables are:

- $x_1(t)$: first bloom date;
- $x_2(t)$: full bloom date;
- $L(t) = x_2(t) - x_1(t)$: bloom duration;
- $F(t)$: accumulated heat forcing;
- $C(t)$: accumulated chilling.

A candidate process description is:

$$
\frac{dx_1}{dt} = f_1(F, C, latitude, species)
$$

$$
\frac{dx_2}{dt} = f_2(F, C, latitude, species)
$$

or, more practically, a threshold model in which $x_1$ and $x_2$ are the dates when forcing crosses two biological thresholds.

Directly estimating $dx/dt$ from sparse annual observations is noisy. Use derivatives for visualization, but use threshold-crossing or state-space models for inference.

## Planned Experiments

### Experiment 1: Rebuild the canonical station-year dataset

**Goal:** Remove duplicated parsing logic and create one trusted input table.

**Output:** `data/station_year_phenology.csv` plus a validation report.

**Success gate:** no duplicate station-year rows, no unexplained negative durations, complete species and coordinate audit.

**Status:** Complete. [build_station_year_table.py](../scripts/build_station_year_table.py) now writes [station_year_phenology.csv](../data/station_year_phenology.csv) and [station_year_validation.txt](../data/station_year_validation.txt). The table has 7,446 rows across 102 stations, zero duplicate station-years and zero negative datetime durations. Ninety stations have at least 15 eligible observations for trend analysis. The 11 stations without coordinates are outside the 91-station main coordinate table and are excluded from the geographic main analysis.

**Data-readiness decision:** The source is usable but not complete at every station-year. The first- and full-bloom files differ in 175 cells because one stage is sometimes missing. The canonical table preserves these gaps, flags the single zero-duration observation, and requires paired dates for duration and physical-model analyses.

### Experiment 2: Expand temperature coverage

**Goal:** Obtain February, March and daily temperatures for stations spanning the duration groups and latitude range.

**Priority stations:** northern shortening sites, southern lengthening sites, central transition sites and Kyoto.

**Output:** station-weather table with source metadata.

**Success gate:** at least 20 to 30 stations with comparable weather records and documented coverage.

**Status:** Complete for the planned station set. Official JMA daily observations were collected for all 20 stations from 1953-2024, producing 85,216 daily rows and 1,355 eligible joined station-years. Nara lacks February/March 1953 records at the JMA source. The earlier Open-Meteo dataset remains a comparison dataset, not the preferred physical-model input.

**Focused station result:** [station_physical_analysis.py](../scripts/station_physical_analysis.py) now prints the full 19-station temperature table and latitude-duration table. The four raw annual restoring-force fits are weak, so this branch is diagnostic rather than the main model. The fixed Kyoto degree-day comparison uses a chronological train/test split and remains a simple secondary mechanism.

**Reference-paper adjustment:** The next modelling step should be a small temperature-forced moving-equilibrium comparison, not a logistic or tipping-point model. It should be evaluated against the existing per-station temperature regression using the same held-out years.

**JMA weather result:** Rerun the station sensitivity, degree-day and moving-equilibrium models using [station_year_weather_jma.csv](../data/station_year_weather_jma.csv), then compare the coefficients and held-out errors with the Open-Meteo versions.

**JMA rerun status:** Complete. JMA preserves the broad regional duration-temperature pattern, but the moving-equilibrium model is not better than the matched baseline and the fixed 400-degree model performs worse than the linear model out of sample. Further physical-model work would require calibration and broader biological inputs; it is outside the trimmed final scope.

**Final model decision:** Adopt the simple empirical response $D = a - bT_{March}$ as the project model. For Kyoto JMA data, $D = 119.55 - 2.878T_{March}$ with $R^2 = 0.720$. Keep degree-day and moving-equilibrium models as documented exploratory comparisons, not as adopted final equations.

### Experiment 3: Parameter grid for degree-day models

**Goal:** Find whether calibrated heat accumulation beats the current 400-degree baseline.

**Models:** first bloom and full bloom separately, then shared-threshold model.

**Metrics:** out-of-sample RMSE, mean bias, median absolute error, error by latitude and species.

**Success gate:** parameters selected on training data and evaluated on an untouched test period.

### Experiment 4: Add chilling

**Goal:** Test whether cold exposure explains regional residuals left by the heat-only model.

**Output:** comparison of heat-only, chilling-only and chilling-plus-forcing models.

**Success gate:** improvement must be visible on held-out years and not only in fitted RMSE.

### Experiment 5: Joint duration model

**Goal:** Explain why first-to-full-bloom duration differs by region.

**Candidate models:**

- threshold difference model;
- mixed-effects regression;
- hierarchical Bayesian model if uncertainty and computation are manageable.

**Success gate:** duration predictions improve over a station-specific trend baseline, and the regional effect remains after temperature and chilling controls.

### Experiment 6: Robustness and dependence

**Goal:** Ensure the result is not an artefact of selected stations or years.

**Checks:**

- multiple common windows;
- leave-one-station-region-out analysis;
- clustered or spatially robust uncertainty;
- species-specific fits;
- active versus discontinued stations;
- nonlinear temperature terms;
- sensitivity to coordinate and weather source.

### Experiment 7: Dynamical-equation presentation

**Goal:** Produce a final equation that is biologically interpretable and empirically tested.

**Preferred final form:**

> Bloom occurs when accumulated forcing, after satisfying a chilling requirement, crosses a species- and stage-specific threshold.

Report the equation, parameter estimates, confidence intervals, validation RMSE and failure modes.

## Recommended Order of Work

### Immediate next session

1. Build the canonical station-year table.
2. Add a species-confidence column and explicitly mark `Not stated` as assumed Yoshino.
3. Produce one validation report for dates, duration, coordinates and station coverage.
4. Do not change the main conclusions yet.

### Next 2 to 3 sessions

1. Expand weather coverage to at least 20 stations.
2. Obtain daily data for a consistent set of stations.
3. Fit the degree-day parameter grid with blocked time validation.
4. Compare first-bloom and full-bloom thresholds.

### Following sessions

1. Add chilling metrics.
2. Fit a joint first/full bloom model.
3. Test mixed-effects or hierarchical regional effects.
4. Evaluate whether duration is explained by threshold separation.

### Final phase

1. Run robustness checks.
2. Freeze the final dataset and parameter choices.
3. Update [research_log.md](research_log.md) with each accepted or rejected hypothesis.
4. Create one reproducible pipeline and a final report.

## Model Selection Rules

- Prefer the simplest model that improves held-out prediction.
- Never select a threshold using the test years.
- Compare all physical models against the same baseline and test period.
- Report error in days, not only $R^2$.
- Keep observed and reconstructed Kyoto temperatures separate.
- Do not pool species without testing whether their parameters differ.
- Treat station shares and regional patterns as correlated evidence, not independent replications.
- Do not call a model physical merely because it contains temperature. Explain its biological mechanism and test its predictions.

## Expected Final Deliverables

1. Canonical cleaned station-year dataset.
2. Canonical weather dataset with source metadata.
3. Official coordinate table and provenance script.
4. Calibrated degree-day model for first and full bloom.
5. Chilling-plus-forcing comparison.
6. Joint duration or threshold-separation model.
7. Spatially aware uncertainty analysis.
8. Final figures and report.
9. Updated research log with hypotheses and decisions.

## Relation To Existing Files

- [jma_deep_checks.py](../scripts/jma_deep_checks.py): current common-window and species checks.
- [jma_window_robustness.py](../scripts/jma_window_robustness.py): multi-window trend sensitivity.
- [jma_latitude_analysis.py](../scripts/jma_latitude_analysis.py): current geographic regressions.
- [jma_temperature_sensitivity.py](../scripts/jma_temperature_sensitivity.py): current eight-station temperature associations.
- [step4_physical_equation.py](../scripts/step4_physical_equation.py): current 400-degree baseline.
- [update_jma_coordinates.py](../scripts/update_jma_coordinates.py): official JMA coordinate updater.
- [research_log.md](research_log.md): cumulative hypotheses and discoveries.

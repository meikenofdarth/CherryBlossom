# Cherry Blossom Bloom Dynamics: Research Log

This document records the project's workflow, hypotheses, tests, results and decisions. Add a dated entry when a substantial analysis changes what we believe about the data or the research question. Keep exploratory results and rejected hypotheses here rather than deleting them.

## How To Use This Log

For each major analysis, record:

- **Question or hypothesis:** what we expected to find.
- **Test:** data, model and time window used.
- **Result:** the numerical or visual outcome.
- **Decision:** how the result affects the project.
- **Files:** scripts, data and plots used.

The project summary in [project_summary.md](project_summary.md) is the current presentation and report overview. This log is the more detailed history behind it.

The forward-looking modelling architecture is in [research_architecture_plan.md](research_architecture_plan.md). Use it to choose the next experiment, then record the result here.

## Current Workflow

1. **Understand the assignment and sources.** The original goal is to study first bloom, full bloom and their rates of change across time and stations, then propose a temperature-based dynamical equation.
2. **Prepare Kyoto data.** Clean the Aono bloom and temperature records, distinguish observed from reconstructed temperatures, and analyse Kyoto's long historical record.
3. **Prepare JMA station data.** Reshape first-bloom and full-bloom tables from wide to long format, parse dates, normalize DOY, calculate actual durations and identify species groups.
4. **Run station trends.** Estimate first-bloom, full-bloom and duration trends with confidence intervals.
5. **Control comparability.** Use a common time window and minimum valid-year requirement to reduce station-window bias.
6. **Verify geography.** Replace approximate geocoded coordinates with official JMA station-master coordinates.
7. **Test regional structure.** Regress station averages and trends against latitude and inspect duration groups.
8. **Add temperature data.** Download February and March temperature summaries for selected stations and compare bloom timing and duration with temperature.
9. **Test a physical model.** Compare a thermal-sum rule with a simple statistical temperature model.
10. **Report cautiously.** Separate observed evidence from reconstructed data, exploratory analyses, unsupported causal claims and legacy outputs.

## Hypothesis Register

### H1: Kyoto bloom dates have changed over the long historical record

**Test:** Regress Aono Kyoto full-bloom DOY against year, with separate pre-1850, post-1850 and post-1950 periods.

**Result:** The pre-1850 trend is small at **+0.31 days/century**. The post-1850 trend is strongly earlier at **−7.53 days/century**. The post-1950 estimate is **−7.93 days/century**, with overlapping uncertainty relative to the post-1850 estimate.

**Decision:** **Supported for the modern period.** The data do not show a strong uniform trend throughout the entire 1200-year record, but they do show a clear modern advance, especially after approximately 1850.

**Files:** [kyoto_master_analysis.py](../scripts/kyoto_master_analysis.py), [kyoto_results.txt](../data/kyoto_results.txt), [step1_doy_vs_year.png](../plots/step1_doy_vs_year.png), [doy_trends_split.png](../plots/doy_trends_split.png).

### H2: Warmer March temperatures are associated with earlier Kyoto bloom

**Test:** Regress Kyoto bloom DOY against March temperature using only the 118 years with observed temperatures.

**Result:** Temperature sensitivity is **−2.99 days per degree Celsius**, 95% CI **[−3.39, −2.60]**, with $R^2 = 0.6623$.

**Decision:** **Strongly supported as an observational association.** It is not a claim that temperature is the only cause.

**Files:** [kyoto_master_analysis.py](../scripts/kyoto_master_analysis.py), [kyoto_corrected_analysis.py](../scripts/kyoto_corrected_analysis.py), [kyoto_results.txt](../data/kyoto_results.txt), [kyoto_observed_doy_vs_temperature.png](../plots/kyoto_observed_doy_vs_temperature.png).

### H3: The original very high Kyoto temperature fit was valid

**Test:** Review the first analysis, which mixed observed temperatures with pre-instrumental temperatures reconstructed partly from bloom dates.

**Result:** The apparently very high fit was circular because bloom dates contributed to the reconstructed temperature predictor.

**Decision:** **Rejected.** Temperature claims use observed-temperature years only. The old mixed-temperature figures are retained as exploratory history but excluded from final evidence.

**Files:** [step2_doy_vs_temp.png](../plots/step2_doy_vs_temp.png), [step2_temp_residuals.png](../plots/step2_temp_residuals.png), [kyoto_corrected_analysis.py](../scripts/kyoto_corrected_analysis.py).

### H4: The observed Kyoto temperature model has major residual dependence or an unexplained recent shift

**Test:** Inspect residuals versus year, calculate Durbin-Watson, and test post-1990 residuals.

**Result:** Durbin-Watson is **2.03**. Post-1990 residual mean is **−0.28 days**, with $p = 0.63$.

**Decision:** **No strong evidence found.** The model is not perfect, but these checks do not show strong autocorrelation or a statistically clear recent residual shift.

**Files:** [kyoto_master_analysis.py](../scripts/kyoto_master_analysis.py), [kyoto_corrected_analysis.py](../scripts/kyoto_corrected_analysis.py), [residuals_vs_year_observed.png](../plots/residuals_vs_year_observed.png).

### H5: The temperature sensitivity changed after 1950

**Test:** Add a temperature-by-post-1950 interaction to the observed Kyoto regression.

**Result:** Interaction p-value is **0.22**.

**Decision:** **Not supported by this test.** There is no strong evidence that the March-temperature slope changed after 1950.

**Files:** [kyoto_master_analysis.py](../scripts/kyoto_master_analysis.py), [kyoto_results.txt](../data/kyoto_results.txt).

### H6: Most Japanese stations show earlier full bloom

**Test:** Calculate full-bloom trends for JMA stations and repeat them in common windows with at least 40 valid years.

**Result:** In 1961-2010, **98.6%** of Not stated stations and **87.5%** of Sargent stations have negative full-bloom trends. The Not stated median is **−1.27 days/decade** and the Sargent median is **−1.09 days/decade**.

The result is stable across additional windows. For Not stated stations, the negative-trend shares are **98.6%** in 1961-2010, **98.0%** in 1971-2020 and **97.9%** in 1976-2025. The median trends are **−1.27, −1.36 and −1.62 days/decade**.

**Decision:** **Strongly supported as a consistent station-network pattern.** This is reported using station shares and medians, not as 90 independent tests.

**Files:** [jma_deep_checks.py](../scripts/jma_deep_checks.py), [jma_window_robustness.py](../scripts/jma_window_robustness.py), [jma_trend_histogram.py](../scripts/jma_trend_histogram.py), [histogram_full_trends.png](../plots/histogram_full_trends.png).

### H7: Bloom duration has no meaningful geographic structure

**Test:** Compare duration trends across stations, then regress mean bloom date, full-bloom trend and duration trend against latitude for 73 Yoshino-group stations.

**Result:** Duration trends are more negative at higher latitudes. The latitude slope is **−0.104 days/decade per degree**, 95% CI **[−0.134, −0.073]**, with $R^2 = 0.395$. Southern and central stations more often lengthen, while northern stations more often shorten or remain flat.

The national duration median is window-sensitive: Not stated values are **+0.30, +0.24 and +0.10 days/decade** in the three windows above.

**Decision:** **Rejected in its simple national form.** A near-zero national median does not mean duration is spatially uniform. The regional pattern is promising but needs a model that accounts for temperature, latitude, station history and shared weather.

**Files:** [jma_latitude_analysis.py](../scripts/jma_latitude_analysis.py), [jma_window_robustness.py](../scripts/jma_window_robustness.py), [latitude_regressions.png](../plots/latitude_regressions.png), [aikawa_trend.png](../plots/aikawa_trend.png), [sparse_trend.png](../plots/sparse_trend.png).

### H8: The station coordinates are accurate enough for geographic analysis

**Test:** Compare the existing table with the official JMA AMeDAS station master.

**Result:** Several approximate coordinates were materially wrong, including Aikawa, Fukue, Kyoto, Nagano and the Osaka/Okayama pair. The table was replaced with official JMA coordinates. It now contains 91 rows, no missing coordinates and no duplicate coordinate pairs.

**Decision:** **Original hypothesis rejected; corrected table adopted.** All latitude results after this correction use the official station master.

**Files:** [update_jma_coordinates.py](../scripts/update_jma_coordinates.py), [station_coords_template.csv](../data/JMA-kaggle_dataest/station_coords_template.csv).

### H9: Warmer February-March conditions lengthen bloom duration everywhere

**Test:** Regress duration against mean February-March temperature for eight stations.

**Result:** The response differs by region. Kyoto is **+1.41 days per degree Celsius**, Fukuoka **+1.55**, Kagoshima **+1.06** and Osaka **+1.20**. Aomori is **−0.14**, Asahikawa **−0.14** and Yamagata **−0.07** days per degree Celsius.

**Decision:** **Rejected as a universal hypothesis.** The results are consistent with a regional response, but this remains preliminary because only eight stations have temperature data and the temperatures come from Open-Meteo rather than JMA monthly observations.

**Files:** [fetch_temperatures.py](../scripts/fetch_temperatures.py), [jma_temperature_sensitivity.py](../scripts/jma_temperature_sensitivity.py), [jma_temperatures.csv](../data/jma_temperatures.csv), [temperature_sensitivity.png](../plots/temperature_sensitivity.png).

### H10: A simple 400-degree thermal-sum rule predicts Kyoto bloom better than a statistical temperature model

**Test:** Accumulate positive daily temperatures from February 1 until 400 degree-days are reached. Compare the predicted bloom date with a linear model using mean February-March temperature.

**Result:** The 400-degree rule RMSE is **4.84 days**. The linear comparison model RMSE is **3.24 days** on the fitted comparison data.

**Decision:** **Not supported in the current implementation.** The thermal-sum idea remains biologically meaningful, but the threshold, base temperature, starting date and chilling treatment need calibration. The comparison should later be repeated with out-of-sample evaluation.

**Files:** [step4_physical_equation.py](../scripts/step4_physical_equation.py), [step4_physical_equation.png](../plots/step4_physical_equation.png).

### H11: Aikawa is representative of the national station trend

**Test:** Inspect the Aikawa full-bloom trend plot.

**Result:** Aikawa's trend is approximately **−0.02 days/decade**, essentially flat.

**Decision:** **Rejected as a station-level generalization.** Aikawa is a useful counterexample showing that national consistency does not mean every station has the same trend.

**Files:** [aikawa_trend.png](../plots/aikawa_trend.png).

### H12: The sparsest station can support a strong trend conclusion

**Test:** Inspect Yonaguni Island, with $n = 16$ observations.

**Result:** The plot is highly variable and the trend estimate is low-power.

**Decision:** **Rejected.** Sparse station results are descriptive only and should not carry the main conclusion.

**Files:** [sparse_trend.png](../plots/sparse_trend.png).

### H13: A canonical station-year table can provide one consistent input for later models

**Test:** Parse the JMA first- and full-bloom files once, normalize bloom DOY, calculate duration from actual datetimes, attach species flags and official coordinates, and validate station-year uniqueness.

**Result:** The canonical table contains **7,446 rows across 102 stations**, with zero duplicate station-year rows and zero negative datetime durations. There are **5,674** row-level eligible observations and **90** stations with at least 15 eligible observations for trend analysis. Eleven stations have no coordinate entry because the official main coordinate table contains 91 stations and excludes non-main species or special cases.

**Decision:** **Supported.** The shared table is suitable as the input layer for the next weather and physical-model experiments. Coordinate completeness must still be checked separately for analyses that include excluded species.

**Files:** [build_station_year_table.py](../scripts/build_station_year_table.py), [station_year_phenology.csv](../data/station_year_phenology.csv), [station_year_validation.txt](../data/station_year_validation.txt).

### H14: The current source data are complete and error-free for every station-year

**Test:** Compare the first- and full-bloom source tables cell by cell, audit raw date parsing, check station-year uniqueness, inspect duration ranges, verify coordinates and recompute Kyoto sample counts from the NOAA source files.

**Result:** The JMA files have the same 102 stations and 1953-2025 year columns, with no duplicate source rows or unparseable dates. They differ in 175 station-year cells where one bloom stage is recorded and the other is missing. These are expected partial observations and are excluded from paired analyses. The canonical table has 7,446 unique station-year rows, 6,116 paired bloom records, zero negative durations and one same-day record: Asahikawa 2012, Sargent cherry, both dates May 2. The 91-station coordinate table is complete for every main-analysis eligible station; the 11 missing-coordinate stations are excluded species or Kutchan. Kyoto contains 785 valid flower dates, 125 observed temperature records and 118 overlapping observed-temperature/bloom years, matching the main analysis.

**Decision:** **Partly rejected, dataset usable with explicit missingness flags.** The data are structurally sound for the main paired analyses, but not complete for every station-year. The one zero-duration record is retained and flagged rather than silently changed. Models must state their paired-data requirements and sample sizes.

**Files:** [build_station_year_table.py](../scripts/build_station_year_table.py), [station_year_validation.txt](../data/station_year_validation.txt), [sakura_first_bloom_dates.csv](../data/JMA-kaggle_dataest/sakura_first_bloom_dates.csv), [sakura_full_bloom_dates.csv](../data/JMA-kaggle_dataest/sakura_full_bloom_dates.csv), [kyoto2010flower.txt](../data/kyoto2010flower.txt), [kyoto2010temp.txt](../data/kyoto2010temp.txt).

### H15: The regional duration-temperature pattern survives expanded weather coverage

**Test:** Expand the station weather set from 8 to 20 planned stations, using corrected JMA coordinates and the canonical station-year phenology table. Fit full-bloom DOY against March temperature and duration against mean February-March temperature.

**Result:** Weather data were retrieved for 19 stations, covering 1,301 joined station-years from 1953-2024 with no duplicate rows or missing February/March values. Miyazaki could not be retrieved because the Open-Meteo request failed temporarily. Thirteen of 19 station duration slopes are positive and six are negative. A simple exploratory regression of station-level duration slopes against latitude is negative with $R^2 \approx 0.715$.

**Decision:** **Promising but unresolved.** The expanded result supports the regional hypothesis more clearly than the original eight-station sample, but station-level slopes are correlated evidence, not independent observations. The result needs JMA temperature data or a larger consistently sourced weather dataset and a joint model with spatial dependence.

**Files:** [fetch_temperatures.py](../scripts/fetch_temperatures.py), [build_station_weather_table.py](../scripts/build_station_weather_table.py), [jma_temperature_sensitivity.py](../scripts/jma_temperature_sensitivity.py), [jma_temperatures.csv](../data/jma_temperatures.csv), [station_year_weather.csv](../data/station_year_weather.csv), [station_temperature_sensitivity.csv](../data/station_temperature_sensitivity.csv), [temperature_sensitivity.png](../plots/temperature_sensitivity.png).

### H16: A simple station restoring-force model explains annual bloom dynamics

**Test:** Estimate $d(DOY)/dt$ with `numpy.gradient` using actual observation years, then fit $d(DOY)/dt = -k DOY + c$ for Wakkanai, Kagoshima, Matsumoto and Kyoto.

**Result:** The fits were weak, with $R^2$ values **0.0027, 0.0001, 0.0017 and 0.0010**. The estimated $k$ values were **0.0322, 0.0074, -0.0284 and 0.0203 per year**, with confidence intervals spanning zero. Equilibrium estimates had extremely wide intervals.

**Decision:** **Not supported as a useful raw annual station model.** The phase-space figure remains diagnostic, but annual bloom DOY is dominated by external forcing and noise rather than a simple autonomous restoring force.

**Files:** [station_physical_analysis.py](../scripts/station_physical_analysis.py), [station_restoring_force.csv](../data/station_restoring_force.csv), [station_phase_space_selected.png](../plots/station_phase_space_selected.png).

### H17: The simple 400-degree model beats the linear model on a proper held-out split

**Test:** Use base temperature $0^\circ$C, February 1 start and a fixed 400 degree-day threshold. Compare it with a linear Feb-March temperature model using train years $\leq 1990$ and test years $>1990$.

**Result:** Degree-day RMSE is **4.6820 days in-sample** and **3.6015 days out-of-sample**. The linear model is **3.1264 days in-sample** and **4.2782 days out-of-sample**. Temperatures are Open-Meteo archive data, not JMA observed temperatures.

**Decision:** **Inconclusive but honestly validated.** The fixed degree-day model has lower test RMSE on this split but is not proven generally superior.

**Files:** [station_physical_analysis.py](../scripts/station_physical_analysis.py), [step4_physical_equation.png](../plots/step4_physical_equation.png).

### H18: The reference tipping-point model can be transferred directly to cherry bloom data

**Test:** Compare the supplied Chaos paper's time-dependent logistic/tipping framework with the available annual bloom observations and the station restoring-force experiment.

**Result:** The paper provides useful concepts: state variables, external forcing, moving equilibria, relaxation and parameter-rate effects. However, the cherry data currently show no evidence of multiple equilibria, basin boundaries or tipping. The raw annual restoring-force fits for four stations had $R^2 < 0.003$ and $k$ confidence intervals spanning zero.

**Decision:** **Not directly transferable as a tipping-point claim.** Use the paper to motivate a simple temperature-forced moving-equilibrium model as a future exploratory comparison, not to claim that cherry flowering has already demonstrated a climatic tipping point.

**Files:** [reference_paper_notes.md](reference_paper_notes.md), [jb_etal_chaos_tippingpts.pdf](jb_etal_chaos_tippingpts.pdf), [station_physical_analysis.py](../scripts/station_physical_analysis.py), [station_restoring_force.csv](../data/station_restoring_force.csv).

### H19: A temperature-forced moving-equilibrium model improves station dynamics

**Test:** Fit the simple lagged model

$$
D_{s,t} = a_s + \phi_sD_{s,t-1} + \beta_sT_{s,t} + \gamma_st + e_{s,t}
$$

using only consecutive years, training through 1990 and testing after 1990. Here $\phi_s$ is interpreted as a persistence parameter, not as proof of a stable dynamical equilibrium.

**Result:** All 19 stations produced fits. The median point estimate of the relaxation rate $1-\phi$ is **0.8859 per year**; 18 of 19 relaxation confidence intervals include zero. The median held-out RMSE is **4.4132 days**, compared with **4.5232 days** for the same-split station-specific temperature baseline. The moving-equilibrium model improves test RMSE at 10 of 19 stations. Kyoto has test RMSE **3.0256 days**, versus **4.2597 days** for its baseline.

**Decision:** **Exploratory only.** The model provides a useful bridge to the reference paper's moving-equilibrium language and is slightly better on median held-out error, but the improvement is not decisive and its parameters are uncertain. One station's interval excludes zero, while the other 18 include zero. No tipping point or regime change is demonstrated.

**Files:** [station_moving_equilibrium.py](../scripts/station_moving_equilibrium.py), [station_moving_equilibrium.csv](../data/station_moving_equilibrium.csv), [station_moving_equilibrium.png](../plots/station_moving_equilibrium.png).

### H20: Official JMA daily temperatures can replace the Open-Meteo weather layer

**Test:** Resolve official JMA station identifiers, collect daily February-March observations with a rate-limited streaming downloader, aggregate them to station-year means, and join them to the canonical phenology table.

**Result:** The JMA layer contains **85,216 daily rows** for 20 stations over 1953-2024 and **1,355 eligible joined station-years**. There are 2,878 of 2,880 expected station-month blocks. The two missing blocks are Nara February and March 1953, which return no daily records from JMA. No downloader failures were recorded.

**Decision:** **Supported and adopted.** JMA daily observed temperatures replace Open-Meteo as the preferred weather input for physical-model and station-temperature analyses. Open-Meteo remains a documented comparison layer.

**Files:** [resolve_jma_daily_stations.py](../scripts/resolve_jma_daily_stations.py), [fetch_jma_daily_streaming.py](../scripts/fetch_jma_daily_streaming.py), [build_jma_weather_table.py](../scripts/build_jma_weather_table.py), [jma_daily_observed_streaming.csv](../data/jma_daily_observed_streaming.csv), [jma_observed_temperatures.csv](../data/jma_observed_temperatures.csv), [station_year_weather_jma.csv](../data/station_year_weather_jma.csv), [jma_weather_validation.txt](../data/jma_weather_validation.txt).

### H21: Official JMA temperatures preserve the regional duration pattern

**Test:** Rerun station temperature regressions using `station_year_weather_jma.csv` rather than Open-Meteo data.

**Result:** JMA duration slopes remain positive in Kyoto (**+1.18**), Fukuoka (**+1.37**) and Kagoshima (**+1.10** days/$^\circ$C), and negative in Aomori (**−0.21**), Akita (**−0.10**) and Wakkanai (**−0.28**). Temperature-bloom slopes remain negative at nearly every station.

**Decision:** **Supported as a regional association, with source-corrected coefficients.**

**Files:** [station_physical_analysis.py](../scripts/station_physical_analysis.py), [station_temperature_sensitivity_jma.csv](../data/station_temperature_sensitivity_jma.csv), [station_year_weather_jma.csv](../data/station_year_weather_jma.csv).

### H22: The fixed 400-degree model is accurate with official JMA daily temperatures

**Test:** Use JMA daily Kyoto observations, base temperature $0^\circ$C, February 1 start, 400 degree-day threshold, and train years $\leq 1990$ versus test years $>1990$.

**Result:** The degree-day model has in-sample RMSE **9.3941 days** and out-of-sample RMSE **7.2938 days**. The matched linear model has **2.3138** and **4.0473 days**, respectively, using 37 paired Kyoto years.

**Decision:** **Rejected as an accurate fixed model.** It remains a transparent mechanistic baseline, not a final physical equation.

**Files:** [jma_degree_day_model.py](../scripts/jma_degree_day_model.py), [kyoto_jma_degree_day_results.csv](../data/kyoto_jma_degree_day_results.csv).

### H23: The moving-equilibrium model is superior with official JMA temperatures

**Test:** Rerun the moving-equilibrium model and its same-split station-specific temperature baseline with JMA weather.

**Result:** Moving-equilibrium median test RMSE is **4.3176 days**, baseline median is **4.0455 days**, and the moving model improves at 9 of 19 stations. All relaxation confidence intervals include zero.

**Decision:** **Rejected as a final superior model.** Retain as exploratory dynamics framing only.

**Files:** [station_moving_equilibrium.py](../scripts/station_moving_equilibrium.py), [station_moving_equilibrium_jma.csv](../data/station_moving_equilibrium_jma.csv), [station_moving_equilibrium_jma.png](../plots/station_moving_equilibrium_jma.png).

### H24: The two latitude coefficients are duplicate calculations

**Test:** Compare the 73-station regression of duration trend against latitude with the separate 20-station regression of duration-temperature slope against latitude.

**Result:** They use different inputs and are not duplicates. The 73-station duration-trend regression is **−0.1037**, $R^2 = 0.3947$. The 20-station duration-temperature-slope regression is **−0.1175**, 95% CI **[−0.1527, −0.0823]**, $R^2 = 0.7318$.

**Decision:** **Resolved.** Both are exploratory regional associations, but they should be reported as separate analyses with separate tables.

**Files:** [station_duration_slope_latitude_jma.csv](../data/station_duration_slope_latitude_jma.csv), [station_duration_temperature_slope_latitude_jma.csv](../data/station_duration_temperature_slope_latitude_jma.csv), [station_physical_analysis.py](../scripts/station_physical_analysis.py).

### H25: The fixed degree-day RMSE ordering indicates a code bug

**Test:** Recompute the saved JMA degree-day RMSE values directly from [kyoto_jma_degree_day_results.csv](../data/kyoto_jma_degree_day_results.csv), separating fixed degree-day predictions from the linear model fitted only on training years.

**Result:** The reported values reproduce exactly: fixed degree-day RMSE **9.3941** train and **7.2938** test; linear RMSE **2.3138** train and **4.0473** test. The degree-day prediction is fixed and not fitted on the training data, so its test error being lower than its train error is possible by chance and is not, by itself, a bug.

**Decision:** **Resolved, but the model remains weak.** The fixed 400-degree model is not adopted as the final equation because its JMA test error is worse than the linear model.

**Files:** [jma_degree_day_model.py](../scripts/jma_degree_day_model.py), [kyoto_jma_degree_day_results.csv](../data/kyoto_jma_degree_day_results.csv).

### H26: The simple JMA linear temperature equation is the most defensible final model

**Test:** Fit full-bloom DOY against March mean temperature for all 72 Kyoto station-weather years in the official JMA monthly join.

**Result:**

$$
D_{Kyoto} = 119.55 - 2.878T_{March}, \qquad R^2 = 0.720
$$

The slope 95% CI is **[−3.305, −2.450]** days/$^\circ$C. This model is simple, interpretable and supported by independent station-level temperature relationships, but it remains empirical rather than a complete biological process equation.

**Decision:** **Adopt as the project’s final simple physical-response model.** Retain degree-day and moving-equilibrium models as explicitly labelled exploratory comparisons.

**Files:** [station_year_weather_jma.csv](../data/station_year_weather_jma.csv), [station_temperature_sensitivity_jma.csv](../data/station_temperature_sensitivity_jma.csv).

### H27: Apparent phase-space loops depend strongly on smoothing

**Test:** For Kyoto, Wakkanai, Kagoshima and Osaka, analyze first and full bloom separately. Compare cubic smoothing splines with residual budgets of 0, 5, 25 and 100 days-squared per observation against Gaussian kernel smoothers with 3-, 7- and 12-year bandwidths. Derivatives use actual year spacing; annual finite differences are shown as a noisy reference. The script reports fit error, scaled endpoint distance, state-direction reversals and distance from the `s/n=25` spline path.

**Result:** Across these four stations, exact-interpolation splines (`s/n=0`) had a median of 45.5 first-bloom and 46.5 full-bloom direction reversals. At `s/n=25`, the medians fell to 2 and 1, respectively; `s/n=100` gave the same median fit error and reversal counts. Gaussian smoothers with 7-year bandwidth had median reversal counts of 1.5 and 2. Endpoint distances also varied by smoothing choice. Thus, the busy loop geometry is not stable under weak smoothing, while stronger smoothing and the broader kernel estimates yield much simpler paths. This is evidence of smoothing sensitivity, not evidence for or against a biological oscillator.

**Decision:** **Limit-cycle interpretation remains unsubstantiated.** Treat the smooth curves as exploratory phase-space summaries. Continue by separating long-term trends from possible recurrence, then test recurrence in the observations and against independent climate drivers.

**Files:** [phase_space_smoothing_sensitivity.py](../scripts/phase_space_smoothing_sensitivity.py), [phase_space_smoothing_sensitivity.csv](../data/phase_space_smoothing_sensitivity.csv), [station audit](../data/advanced_dynamics_station_audit.csv), [sensitivity plots](../plots/phase_space_smoothing_sensitivity/).

### H28: Detrended annual bloom dates contain candidate periodic peaks, not validated cycles

**Test:** For the same four representative stations, scan sinusoidal fits over periods of 3–30 years in residuals from linear, quadratic and smoothing-spline (`s/n=25`) trend fits. Use actual observation years, retain missing-year gaps, and compare peak periods and the fraction of residual variance explained across detrending methods. The scan is descriptive; it does not calculate a significance level or validate forecasts.

**Result:** Most station/stage peak periods are similar across the three detrending choices, but the strongest candidate explains only about 10–18% of the detrended variance. Wakkanai first bloom is especially trend-sensitive: the linear detrend's largest peak is at the 30-year search boundary, while quadratic and spline detrending peak near 6.7 years. A peak at the boundary is unresolved by this record. The other peaks are exploratory candidates only; no correction for searching many periods or autocorrelation-aware null test has been applied.

**Decision:** **No validated periodic component established.** These results prioritize follow-up recurrence and climate-driver tests, rather than support a limit-cycle claim. Candidate periods should not be reported as estimated biological cycles at this stage.

**Files:** [phase_space_oscillation_screen.py](../scripts/phase_space_oscillation_screen.py), [phase_space_oscillation_screen.csv](../data/phase_space_oscillation_screen.csv), [screen plots](../plots/phase_space_oscillation_screen/).

### H29: Smoothed phase-space paths show repeatable closed cycles

**Test:** For the same four stations, measure start-to-end distance relative to total path length, closest phase-state returns separated by at least eight years, and direction agreement at returns. Apply a prespecified 0.10 scaled-distance threshold to raw finite-difference, spline (`s/n=25`) and Gaussian-kernel (`h=7`) paths. Also compare bloom-date anomalies with matched JMA February-March temperature anomalies after removing linear trends.

**Result:** The median endpoint-distance/path-length ratio is **0.418** for spline paths and **0.328** for Gaussian paths; smaller values indicate closer endpoint return. The smoother paths therefore do not consistently close. Some individual smooth paths have close, similarly directed returns, but these occur in only a subset of station/stage/method combinations. The raw finite-difference paths produce many close pairs, but are jagged and yield overlapping pair counts that should not be interpreted as independent cycles. In the matched climate comparison, the median linear-detrended bloom-temperature correlation is **−0.538** across the eight station/stage pairs; this is descriptive co-variation, not evidence for a periodic driver response.

**Decision:** **No repeatable closed orbit established.** Endpoint proximity and close state returns vary with representation, while raw derivative paths are noisy. The temperature plane supports the already observed inverse bloom-temperature relationship but does not demonstrate a recurring forced cycle.

**Files:** [phase_space_recurrence_audit.py](../scripts/phase_space_recurrence_audit.py), [phase_space_recurrence_audit.csv](../data/phase_space_recurrence_audit.csv), [recurrence plots](../plots/phase_space_recurrence_audit/).

### H30: Periodic models improve held-out bloom-date predictions

**Test:** Compare temperature-only, trend-only, trend-plus-temperature, training-selected trend/temperature/periodic, and one-step AR(1)-plus-trend-plus-temperature models. Use the same JMA-matched consecutive-year observations for each model, train through 1990 and test after 1990. Select each periodic model's period from training data only. The AR model uses the previous observed bloom date and is therefore a one-step forecast, not a recursive long-range forecast.

**Result:** Across eight station/stage pairs, median test RMSE was **4.195 days** for temperature only, **6.098** for trend only, **4.502** for trend plus temperature, **4.823** for trend, temperature and a selected period, and **4.446** for one-step AR plus trend and temperature. The periodic model beat temperature only at **1 of 8** pairs. AR beat temperature only at 4 of 8 pairs, but had higher median error. Each test set had 34 years; training samples ranged from 26 to 37 years because the comparison requires consecutive matched observations.

**Decision:** **No held-out evidence that a periodic bloom component improves prediction.** Temperature-only remains the strongest median baseline in this small representative set. The result is exploratory, with four stations and one temporal split; the periodic search is not evidence for an autonomous limit cycle.

**Files:** [validate_recurrence_models.py](../scripts/validate_recurrence_models.py), [holdout scores](../data/recurrence_model_holdout_scores.csv), [test predictions](../data/recurrence_model_holdout_predictions.csv), [prediction plots](../plots/recurrence_model_holdout/).

## Important Data and Analysis Decisions

- Use actual datetime subtraction for duration, especially for Taiwan cherry dates crossing the New Year.
- Use a leap-year-normalized DOY for bloom-date comparisons.
- Exclude Taiwan cherry and Kurile cherry from the main Yoshino/Sargent comparison.
- Exclude Kutchan because the observed species changed in 1995.
- Treat Not stated as Yoshino only as a documented working assumption until confirmed from the source metadata.
- Use official JMA coordinates rather than general geocoding.
- Use observed Kyoto temperatures only for temperature inference.
- Report station medians, ranges and directional shares because stations are spatially correlated.
- Keep thermal-sum modelling separate from the descriptive trend analysis until it is calibrated and evaluated out of sample.

## Current Open Questions

1. Does the regional duration pattern remain after using JMA monthly temperatures for a larger set of stations?
2. Does a spatial or hierarchical model explain duration better than separate station regressions?
3. What species does the source label `Not stated` actually represent?
4. Do the recent Aono Kyoto observations overlap the JMA Kyoto station record?
5. Which thermal-sum threshold, base temperature, starting date and chilling requirement work best out of sample?
6. Does the duration result survive additional windows and station-history controls?
7. Can all final analyses be assembled into one reproducible pipeline without legacy scripts?
8. Does a calibrated degree-day model improve held-out bloom-date predictions over the current linear baseline?
9. Does the regional duration-temperature result remain after adding Miyazaki and using a joint spatial model?
10. Can a simple temperature-forced moving-equilibrium model improve held-out predictions without requiring a tipping-point claim?
11. Does the moving-equilibrium model outperform a same-split station-specific temperature baseline?

## Update Protocol

When a substantial new analysis is completed:

1. Add a new hypothesis entry with the next `H` number, or update an existing hypothesis if it directly tests the same claim.
2. Record the exact data period, sample size and model used.
3. Give the numerical result and distinguish association from causation.
4. State whether the hypothesis was supported, rejected or left unresolved.
5. Link the script, data file and plot.
6. Update the open-question list and the project summary if the main conclusion changes.

## Log History

- **2026-09-21:** Created the research log and recorded the Kyoto circularity correction, station trend results, coordinate correction, latitude analysis, temperature sensitivity, thermal-sum test, station counterexamples and multi-window robustness results.
- **2026-09-21:** Built and validated the canonical station-year phenology table as the first experiment in the research architecture.
- **2026-10-01:** Completed the official JMA daily weather layer, reran the temperature and dynamics models, resolved the separate latitude regressions, adopted the simple JMA Kyoto temperature-response equation, and created the next-chat handoff.
- **2026-10-03:** Audited coverage for the 102 advanced-dynamics stations and completed a four-station smoothing-sensitivity comparison for first and full bloom.
- **2026-10-03:** Compared candidate periodic components after three detrending methods for first and full bloom at the four representative stations.
- **2026-10-03:** Audited endpoint closure, separated phase-state returns and the bloom-temperature anomaly plane for the four representative stations.
- **2026-10-03:** Compared trend, JMA temperature, periodic and one-step AR candidates on matched held-out years for first and full bloom at the four representative stations.

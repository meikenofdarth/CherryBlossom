import pandas as pd


DAILY_FILE = 'data/jma_daily_observed_streaming.csv'
PHENOLOGY_FILE = 'data/station_year_phenology.csv'
MONTHLY_OUTPUT = 'data/jma_observed_temperatures.csv'
JOINED_OUTPUT = 'data/station_year_weather_jma.csv'
VALIDATION_OUTPUT = 'data/jma_weather_validation.txt'


def main():
    daily = pd.read_csv(DAILY_FILE, parse_dates=['Date'])
    monthly = (
        daily.groupby(['Site Name', 'Year', 'Month'], as_index=False)['Temp']
        .mean()
        .pivot(index=['Site Name', 'Year'], columns='Month', values='Temp')
        .reset_index()
        .rename(columns={2: 'Feb_Temp', 3: 'Mar_Temp'})
    )
    monthly['Feb_Mar_Temp'] = monthly[['Feb_Temp', 'Mar_Temp']].mean(axis=1)
    monthly['Temperature_Source'] = 'JMA daily observed'
    monthly.to_csv(MONTHLY_OUTPUT, index=False)

    phenology = pd.read_csv(PHENOLOGY_FILE)
    eligible = phenology[phenology['Main_Analysis_Eligible']].copy()
    joined = eligible.merge(
        monthly,
        on=['Site Name', 'Year'],
        how='inner',
        validate='one_to_one',
    )
    joined.to_csv(JOINED_OUTPUT, index=False)

    expected_blocks = 20 * 72 * 2
    actual_blocks = daily[['Site Name', 'Year', 'Month']].drop_duplicates().shape[0]
    missing_months = int(joined[['Feb_Temp', 'Mar_Temp']].isna().any(axis=1).sum())
    lines = [
        f'Daily rows: {len(daily)}',
        f'Daily stations: {daily["Site Name"].nunique()}',
        f'Daily year range: {int(daily["Year"].min())}-{int(daily["Year"].max())}',
        f'Month blocks: {actual_blocks}/{expected_blocks}',
        f'Monthly station-years: {len(monthly)}',
        f'Joined eligible station-years: {len(joined)}',
        f'Joined stations: {joined["Site Name"].nunique()}',
        f'Joined rows missing Feb/Mar: {missing_months}',
        'Missing month blocks by station:',
    ]
    expected = {
        (site, year, month)
        for site in daily['Site Name'].unique()
        for year in range(1953, 2025)
        for month in (2, 3)
    }
    actual = set(map(tuple, daily[['Site Name', 'Year', 'Month']].drop_duplicates().itertuples(index=False, name=None)))
    lines.extend(str(block) for block in sorted(expected - actual))
    with open(VALIDATION_OUTPUT, 'w') as report:
        report.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'Wrote {MONTHLY_OUTPUT}')
    print(f'Wrote {JOINED_OUTPUT}')
    print(f'Wrote {VALIDATION_OUTPUT}')


if __name__ == '__main__':
    main()

import pandas as pd


PHENOLOGY_FILE = 'data/station_year_phenology.csv'
TEMPERATURE_FILE = 'data/jma_temperatures.csv'
OUTPUT = 'data/station_year_weather.csv'
REPORT = 'data/station_year_weather_validation.txt'


def main():
    phenology = pd.read_csv(PHENOLOGY_FILE)
    temperatures = pd.read_csv(TEMPERATURE_FILE)

    temperatures['Feb_Mar_Temp'] = (
        temperatures['Feb_Temp'] + temperatures['Mar_Temp']
    ) / 2
    temperatures['Temperature_Source'] = 'Open-Meteo archive'

    eligible = phenology[phenology['Main_Analysis_Eligible']].copy()
    joined = eligible.merge(
        temperatures,
        on=['Site Name', 'Year'],
        how='inner',
        validate='one_to_one',
    )

    joined.to_csv(OUTPUT, index=False)
    report_lines = [
        f'Phenology eligible rows: {len(eligible)}',
        f'Temperature stations available: {temperatures["Site Name"].nunique()}',
        f'Joined station-year rows: {len(joined)}',
        f'Joined stations: {joined["Site Name"].nunique()}',
        f'Year range: {int(joined["Year"].min())}-{int(joined["Year"].max())}',
        f'Duplicate station-year rows: {joined.duplicated(["Site Name", "Year"]).sum()}',
        f'Missing temperature values: {joined[["Feb_Temp", "Mar_Temp"]].isna().any(axis=1).sum()}',
        'Joined rows by species:',
        joined.groupby('Species')['Site Name'].nunique().to_string(),
        'Stations without temperature coverage:',
        '\n'.join(sorted(set(eligible['Site Name']) - set(temperatures['Site Name']))),
    ]
    with open(REPORT, 'w') as report:
        report.write('\n'.join(report_lines) + '\n')

    print('\n'.join(report_lines))
    print(f'Wrote {OUTPUT}')
    print(f'Wrote {REPORT}')


if __name__ == '__main__':
    main()
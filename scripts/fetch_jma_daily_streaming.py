import os
import time
from html.parser import HTMLParser

import pandas as pd
import requests


STATION_FILE = 'data/jma_daily_station_ids.csv'
OUTPUT = 'data/jma_daily_observed_streaming.csv'
REQUEST_INTERVAL = 1.0


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.rows = []
        self.row = []
        self.text = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_row = True
            self.row = []
        elif self.in_row and tag in ('td', 'th'):
            self.in_cell = True
            self.text = ''

    def handle_data(self, data):
        if self.in_cell:
            self.text += data

    def handle_endtag(self, tag):
        if self.in_row and tag in ('td', 'th'):
            self.row.append(' '.join(self.text.split()))
            self.in_cell = False
        elif tag == 'tr' and self.in_row:
            if self.row:
                self.rows.append(self.row)
            self.in_row = False


def parse_month(html, station, year, month):
    parser = TableParser()
    parser.feed(html)
    records = []
    for row in parser.rows:
        if not row or not row[0].isdigit() or len(row) < 9:
            continue
        try:
            mean_temp = float(row[6])
        except ValueError:
            continue
        records.append({
            'Site Name': station['Site Name'],
            'Date': pd.Timestamp(year=year, month=month, day=int(row[0])),
            'Temp': mean_temp,
            'Year': year,
            'Month': month,
            'Source': 'JMA daily observed',
            'Prec_No': station['Prec_No'],
            'Block_No': station['Block_No'],
        })
    return pd.DataFrame(records)


def load_completed():
    if not os.path.exists(OUTPUT):
        return set()
    existing = pd.read_csv(OUTPUT, usecols=['Site Name', 'Year', 'Month'])
    return set(map(tuple, existing.drop_duplicates().itertuples(index=False, name=None)))


def append_rows(data):
    if data.empty:
        return
    data.to_csv(OUTPUT, mode='a', header=not os.path.exists(OUTPUT), index=False)


def main():
    start_year = int(os.environ.get('JMA_START_YEAR', '1953'))
    end_year = int(os.environ.get('JMA_END_YEAR', '2024'))
    stations = pd.read_csv(STATION_FILE).to_dict('records')
    completed = load_completed()
    session = requests.Session()
    session.headers.update({'User-Agent': 'SakuraBloomResearch/1.0'})
    failures = []

    for station in stations:
        for year in range(start_year, end_year + 1):
            for month in (2, 3):
                key = (station['Site Name'], year, month)
                if key in completed:
                    continue
                try:
                    response = session.get(
                        'https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php',
                        params={
                            'prec_no': station['Prec_No'],
                            'block_no': station['Block_No'],
                            'year': year,
                            'month': month,
                            'day': '',
                            'view': 'p1',
                        },
                        timeout=30,
                    )
                    response.raise_for_status()
                    if 'ページを表示することが出来ませんでした' in response.text:
                        raise RuntimeError('JMA returned an error page')
                    rows = parse_month(response.text, station, year, month)
                    append_rows(rows)
                    completed.add(key)
                    print(f'{station["Site Name"]} {year}-{month:02d}: {len(rows)} rows', flush=True)
                except Exception as error:
                    failures.append({**station, 'Year': year, 'Month': month, 'Error': str(error)})
                    print(f'FAILED {station["Site Name"]} {year}-{month:02d}: {error}', flush=True)
                time.sleep(REQUEST_INTERVAL)

    if failures:
        pd.DataFrame(failures).to_csv('data/jma_daily_streaming_failures.csv', index=False)
        print(f'Failures: {len(failures)}; see data/jma_daily_streaming_failures.csv')
    else:
        print('Failures: 0')


if __name__ == '__main__':
    main()

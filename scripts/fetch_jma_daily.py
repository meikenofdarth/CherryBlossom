import os
import time
from html.parser import HTMLParser

import pandas as pd
import requests


STATION_FILE = 'data/jma_daily_station_ids.csv'
CACHE_DIR = 'data/jma_daily_cache'
OUTPUT = 'data/jma_daily_observed.csv'
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


def parse_month(html, year, month, station):
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


def fetch_month(session, station, year, month):
    site = station['Site Name']
    cache_file = f'{CACHE_DIR}/{site}_{year}_{month:02d}.html'
    if os.path.exists(cache_file):
        with open(cache_file, encoding='utf-8') as cached:
            return cached.read()
    url = 'https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php'
    params = {
        'prec_no': station['Prec_No'],
        'block_no': station['Block_No'],
        'year': year,
        'month': month,
        'day': '',
        'view': 'p1',
    }
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    if 'ページを表示することが出来ませんでした' in response.text:
        raise RuntimeError(f'JMA returned an error page for {site} {year}-{month:02d}')
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as cache:
        cache.write(response.text)
    time.sleep(REQUEST_INTERVAL)
    return response.text


def main():
    years = range(int(os.environ.get('JMA_START_YEAR', '2020')), int(os.environ.get('JMA_END_YEAR', '2020')) + 1)
    months = (2, 3)
    stations = pd.read_csv(STATION_FILE).to_dict('records')
    session = requests.Session()
    session.headers.update({'User-Agent': 'SakuraBloomResearch/1.0'})
    records = []
    failures = []
    for station in stations:
        for year in years:
            for month in months:
                try:
                    html = fetch_month(session, station, year, month)
                    month_data = parse_month(html, year, month, station)
                    records.append(month_data)
                    print(f'{station["Site Name"]} {year}-{month:02d}: {len(month_data)} rows')
                except Exception as error:
                    failures.append({**station, 'Year': year, 'Month': month, 'Error': str(error)})
                    print(f'FAILED {station["Site Name"]} {year}-{month:02d}: {error}')
    if records:
        result = pd.concat(records, ignore_index=True).drop_duplicates(['Site Name', 'Date'])
        result.to_csv(OUTPUT, index=False)
        print(f'Wrote {len(result)} rows to {OUTPUT}')
    if failures:
        pd.DataFrame(failures).to_csv('data/jma_daily_failures.csv', index=False)
        print(f'Failures: {len(failures)}; wrote data/jma_daily_failures.csv')
    else:
        print('Failures: 0')


if __name__ == '__main__':
    main()

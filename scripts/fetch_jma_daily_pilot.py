import os
import time
from html.parser import HTMLParser

import pandas as pd
import requests


BASE_URL = 'https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php'
OUTPUT = 'data/jma_daily_kyoto_pilot.csv'
CACHE_DIR = 'data/jma_daily_cache'
PREC_NO = 61
BLOCK_NO = 47759
YEARS = range(2020, 2021)
MONTHS = (2, 3)
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


def parse_month(html, year, month):
    parser = TableParser()
    parser.feed(html)
    daily_rows = []
    for row in parser.rows:
        if not row or not row[0].isdigit() or len(row) < 9:
            continue
        day = int(row[0])
        try:
            mean_temp = float(row[6])
        except ValueError:
            continue
        daily_rows.append({
            'Date': pd.Timestamp(year=year, month=month, day=day),
            'Temp': mean_temp,
            'Year': year,
            'Month': month,
            'Source': 'JMA daily observed',
            'Prec_No': PREC_NO,
            'Block_No': BLOCK_NO,
        })
    return pd.DataFrame(daily_rows)


def fetch_month(session, year, month):
    cache_file = f'{CACHE_DIR}/kyoto_{year}_{month:02d}.html'
    if os.path.exists(cache_file):
        return open(cache_file, encoding='utf-8').read()
    params = {
        'prec_no': PREC_NO,
        'block_no': BLOCK_NO,
        'year': year,
        'month': month,
        'day': '',
        'view': 'p1',
    }
    response = session.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    if 'ページを表示することが出来ませんでした' in response.text:
        raise RuntimeError(f'JMA returned an error page for {year}-{month:02d}')
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as cache:
        cache.write(response.text)
    time.sleep(REQUEST_INTERVAL)
    return response.text


def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'SakuraBloomResearch/1.0'})
    records = []
    for year in YEARS:
        for month in MONTHS:
            html = fetch_month(session, year, month)
            month_data = parse_month(html, year, month)
            print(f'{year}-{month:02d}: {len(month_data)} daily records')
            records.append(month_data)
    daily = pd.concat(records, ignore_index=True).drop_duplicates('Date')
    daily.to_csv(OUTPUT, index=False)
    print(f'Wrote {len(daily)} rows to {OUTPUT}')
    print(daily.head().to_string(index=False))
    print(daily.groupby('Month')['Temp'].agg(['count', 'mean']).to_string())


if __name__ == '__main__':
    main()

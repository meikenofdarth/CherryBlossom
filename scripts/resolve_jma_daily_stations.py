import re
import time
from html.parser import HTMLParser

import pandas as pd
import requests


OUTPUT = 'data/jma_daily_station_ids.csv'
REQUEST_INTERVAL = 1.0

TARGETS = {
    'Wakkanai': ('稚内', 11), 'Asahikawa': ('旭川', 12), 'Iwamizawa': ('岩見沢', 15),
    'Urakawa': ('浦河', 22), 'Aomori': ('青森', 31), 'Akita': ('秋田', 32),
    'Yamagata': ('山形', 35), 'Nagano': ('長野', 48), 'Fukui': ('福井', 57),
    'Kyoto': ('京都', 61), 'Nara': ('奈良', 64), 'Osaka': ('大阪', 62),
    'Kobe': ('神戸', 63), 'Matsue': ('松江', 68), 'Kochi': ('高知', 74),
    'Fukuoka': ('福岡', 82), 'Oita': ('大分', 83), 'Miyazaki': ('宮崎', 87),
    'Kagoshima': ('鹿児島', 88), 'Shizuoka': ('静岡', 50),
}


def resolve():
    session = requests.Session()
    session.headers.update({'User-Agent': 'SakuraBloomResearch/1.0'})
    rows = []
    for site, (japanese, prec_no) in TARGETS.items():
        url = 'https://www.data.jma.go.jp/stats/etrn/select/prefecture.php'
        response = session.get(url, params={
            'prec_no': prec_no, 'block_no': '', 'year': '', 'month': '', 'day': '', 'view': '',
        }, timeout=30)
        response.raise_for_status()
        pattern = re.compile(
            rf'<area[^>]*alt="{re.escape(japanese)}"[^>]*href="\.\./index\.php\?prec_no={prec_no}&block_no=(\d+)'
        )
        matches = sorted(set(pattern.findall(response.text)))
        if not matches:
            print(f'{site}: no match for {japanese} in prec_no={prec_no}')
        else:
            block_no = matches[0]
            rows.append({'Site Name': site, 'Japanese Name': japanese, 'Prec_No': prec_no, 'Block_No': block_no})
            print(f'{site}: prec_no={prec_no}, block_no={block_no}')
        time.sleep(REQUEST_INTERVAL)
    pd.DataFrame(rows).to_csv(OUTPUT, index=False)
    print(f'Wrote {len(rows)} station IDs to {OUTPUT}')


if __name__ == '__main__':
    resolve()

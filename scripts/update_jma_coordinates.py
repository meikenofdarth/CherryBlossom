import io
import zipfile

import pandas as pd
import requests


COORDS_FILE = 'data/JMA-kaggle_dataest/station_coords_template.csv'
JMA_MASTER_URL = 'https://www.jma.go.jp/jma/kishou/know/amedas/ame_master.zip'

NAME_MAP = {
    'Abashiri': '網走', 'Aikawa': '相川', 'Akita': '秋田', 'Aomori': '青森',
    'Asahikawa': '旭川', 'Choshi': '銚子', 'Esashi': '江差', 'Fukue': '福江',
    'Fukui': '福井', 'Fukuoka': '福岡', 'Fukushima': '福島', 'Gifu': '岐阜',
    'Hachijojima': '八丈島', 'Hachinohe': '八戸', 'Hakodate': '函館',
    'Hamada': '浜田', 'Hamamatsu': '浜松', 'Hikone': '彦根', 'Hiroo': '広尾',
    'Hiroshima': '広島', 'Iida': '飯田', 'Itsuhara': '厳原',
    'Iwamizawa': '岩見沢', 'Kagoshima': '鹿児島', 'Kanazawa': '金沢',
    'Kobe': '神戸', 'Kochi': '高知', 'Kofu': '甲府', 'Kumagaya': '熊谷',
    'Kumamoto': '熊本', 'Kushiro': '釧路', 'Kyoto': '京都', 'Maebashi': '前橋',
    'Maizuru': '舞鶴', 'Matsue': '松江', 'Matsumoto': '松本',
    'Matsuyama': '松山', 'Mito': '水戸', 'Miyakejima': '三宅島',
    'Miyako': '宮古', 'Miyazaki': '宮崎', 'Monbetsu': '紋別',
    'Morioka': '盛岡', 'Muroran': '室蘭', 'Nagano': '長野',
    'Nagasaki': '長崎', 'Nagoya': '名古屋', 'Nara': '奈良', 'Niigata': '新潟',
    'Nobeoka': '延岡', 'Obihiro': '帯広', 'Oita': '大分', 'Okayama': '岡山',
    'Onahama': '小名浜', 'Osaka': '大阪', 'Oshima': '大島', 'Owase': '尾鷲',
    'Rumoi': '留萌', 'Saga': '佐賀', 'Saigo': '西郷', 'Sakata': '酒田',
    'Sapporo': '札幌', 'Sendai': '仙台', 'Shimonoseki': '下関',
    'Shinjo': '新庄', 'Shiomizumaki': '潮岬', 'Shirakawa': '白河',
    'Shizuoka': '静岡', 'Sumoto': '洲本', 'Takada': '高田',
    'Takamatsu': '高松', 'Takayama': '高山', 'Tanegashima': '種子島',
    'Tateyama': '館山', 'Tokushima': '徳島', 'Tokyo': '東京',
    'Tottori': '鳥取', 'Toyama': '富山', 'Toyooka': '豊岡', 'Tsu': '津',
    'Tsuruga': '敦賀', 'Urakawa': '浦河', 'Utsunomiya': '宇都宮',
    'Uwajima': '宇和島', 'Wajima': '輪島', 'Wakayama': '和歌山',
    'Wakkanai': '稚内', 'Yakushima': '屋久島', 'Yamagata': '山形',
    'Yokohama': '横浜', 'Yonago': '米子',
}


def load_jma_master():
    response = requests.get(JMA_MASTER_URL, timeout=30)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        master_name = archive.namelist()[0]
        with archive.open(master_name) as master_file:
            return pd.read_csv(master_file, encoding='cp932')


def select_station(site, rows, current_latitude, current_longitude):
    rows = rows[rows['種類'].eq('官')].copy()
    if rows.empty:
        raise ValueError(f'{site}: no official JMA station record found')

    rows['Latitude'] = rows['緯度(度)'] + rows['緯度(分)'] / 60
    rows['Longitude'] = rows['経度(度)'] + rows['経度(分)'] / 60
    distance = (rows['Latitude'] - current_latitude) ** 2
    distance += (rows['Longitude'] - current_longitude) ** 2
    return rows.loc[distance.idxmin()]


def main():
    coords = pd.read_csv(COORDS_FILE)
    master = load_jma_master()
    updated = []

    for _, row in coords.iterrows():
        site = row['Site Name']
        jma_name = NAME_MAP.get(site)
        if jma_name is None:
            raise ValueError(f'{site}: missing English-to-Japanese station mapping')
        candidates = master[master['観測所名'].eq(jma_name)]
        selected = select_station(site, candidates, row['Latitude'], row['Longitude'])
        updated.append({
            'Site Name': site,
            'Latitude': round(selected['Latitude'], 4),
            'Longitude': round(selected['Longitude'], 4),
        })

    pd.DataFrame(updated).to_csv(COORDS_FILE, index=False)
    print(f'Updated {len(updated)} coordinates from the official JMA station master.')


if __name__ == '__main__':
    main()
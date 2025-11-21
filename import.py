import sqlite3
import jaconv
from pprint import pprint
import json
from datetime import datetime
import csv

now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

try:
    conn = sqlite3.connect('zenkoku.sqlite3')
except Error as e:
    print(e)

cursor = conn.cursor()

# CREATE prefectures.sql
cursor.execute("SELECT DISTINCT(ken_name),ken_furi,ken_id FROM ad_address WHERE delete_flg=0 ORDER BY ken_id")
records = cursor.fetchall()

i = 0
mapPrefectures = {}

f = open("01_prefectures.sql","w+")
for row in records:
    i = i + 1
    prefId = row[2]
    prefName = row[0].strip()
    if prefName == 'NULL':
        prefName = ''
    prefKata = row[1].strip()
    if prefKata == 'NULL':
        prefKata = '';

    prefHira = ''
    prefRomaji = ''    
    if prefKata != '' :
        prefHira = jaconv.kata2hira(prefKata)
        prefRomaji = jaconv.kana2alphabet(prefHira)

    mapPrefectures.update({prefName:prefId})
    line = "INSERT INTO prefectures (id,name,hiragana,katakana,romaji,created_at,updated_at) VALUES (%s,'%s','%s','%s','%s','%s','%s');" % (i,prefName,prefHira,prefKata,prefRomaji,now,now)
    f.write(line.encode('utf-8').strip().decode() + '\n')

f.close()

# CREATE cities.sql
cursor.execute("SELECT ken_name,city_id,city_name,city_furi FROM ad_address WHERE delete_flg=0 GROUP BY city_id ORDER BY zip")
records = cursor.fetchall()

i = 0
mapCities = {}

f = open("02_cities.sql","w+")
for row in records:
    i = i + 1
    prefId = mapPrefectures[row[0]]
    cityId = row[1]
    cityName = row[2].strip()
    cityName = cityName.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if cityName == 'NULL':
        cityName = ''
    cityKata = row[3].strip()
    if cityKata == 'NULL':
        cityKata = '';

    cityHira = ''
    cityRomaji = ''    
    if cityKata != '' :
        cityHira = jaconv.kata2hira(cityKata)
        cityRomaji = jaconv.kana2alphabet(cityHira)

    mapCities.update({cityId:cityId})
    line = "INSERT INTO cities (id,prefecture_id,name,hiragana,katakana,romaji,created_at,updated_at) VALUES (%s,%s,'%s','%s','%s','%s','%s','%s');" % (cityId,prefId,cityName,cityHira,cityKata,cityRomaji,now,now)
    f.write(line.encode('utf-8').strip().decode() + '\n')

f.close()

# CREATE towns.sql
cursor.execute("SELECT DISTINCT(town_id),city_id,town_name,town_furi,zip FROM ad_address WHERE delete_flg=0 ORDER BY zip")
records = cursor.fetchall()

i = 0
mapTowns = {}
f = open("03_towns.sql","w+")
for row in records:
    i = i + 1
    cityId = row[1]
    cityId = mapCities[cityId]

    townId = row[0]
    townName = row[2].strip()
    townName = townName.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if townName == 'NULL':
        townName = ''
    townKata = row[3].strip()
    townKata = townKata.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if townKata == 'NULL':
        townKata = ''

    townHira = ''
    townRomaji = ''
    if townKata != '':
        townHira = jaconv.kata2hira(townKata)
        townRomaji = jaconv.kana2alphabet(townHira)
        townRomaji = jaconv.z2h(townRomaji, digit=True)

    townZip = row[4].strip()
    townCode = str(townId) + '-' + townZip
    
    if townCode not in mapTowns.keys():
        line = "INSERT INTO towns (id,city_id,name,hiragana,katakana,romaji,zip,created_at,updated_at) VALUES ('%s',%s,'%s','%s','%s','%s','%s','%s','%s');" % (townCode,cityId,townName,townHira,townKata,townRomaji,townZip,now,now)
        f.write(line.encode('utf-8').strip().decode() + '\n')

    mapTowns.update({townCode:townCode})

# CREATE blocks.sql
cursor.execute("SELECT zip || block_name AS block, block_name, block_furi, zip, town_id, id, ken_name, city_name, town_name FROM ad_address WHERE delete_flg=0 GROUP BY block")
records = cursor.fetchall()

i = 0

f = open("04_blocks.sql","w+")
mapBlock = {}
for row in records:
    i = i + 1
    
    prefName = row[6]
    cityName = row[7].strip()
    cityName = cityName.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    townName = row[8].strip()
    townName = townName.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if townName == 'NULL':
        townName = ''
        
    blockId = row[5]
    townId = row[4]
    townZip = row[3].strip()

    townCode0 = str(townId) + '-' + townZip

    townCode = mapTowns[townCode0]

    blockName = row[1].strip()
    blockName = blockName.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if blockName == 'NULL':
        blockName = ''

    blockKata = row[2].strip()
    blockKata = blockKata.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if blockKata == 'NULL':
        blockKata = ''

    blockHira = ''
    blockRomaji = ''
    if blockKata != '' :
        blockHira = jaconv.kata2hira(blockKata)
        blockRomaji = jaconv.kana2alphabet(blockHira)
        blockRomaji = jaconv.z2h(blockRomaji, digit=True)

    fullAddress = prefName + cityName + townName + blockName

    if blockId not in mapBlock.keys():    
        line = "INSERT INTO blocks (id,town_id,name,hiragana,katakana,romaji,full_name,created_at,updated_at) VALUES (%s,'%s','%s','%s','%s','%s','%s','%s','%s');" % (blockId,townCode,blockName,blockHira,blockKata,blockRomaji,fullAddress,now,now)
        f.write(line.encode('utf-8').strip().decode() + '\n')

    mapBlock.update({blockId:blockId})

exit()

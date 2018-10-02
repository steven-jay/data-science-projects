import io
import csv
import psycopg2
import requests
import datetime
#
# conn = psycopg2.connect(dbname='postgres', user='postgres')
# conn.autocommit = True
# cur = conn.cursor()
#
# cur.execute('CREATE DATABASE storms')

def split_time(time):
    return({'hours':time[:2], 'minutes':time[2:4]})

conn = psycopg2.connect(dbname='storms', user='postgres')
cur = conn.cursor()

cur.execute("""DROP TABLE IF EXISTS storm_data""")

cur.execute("""CREATE TABLE storm_data (
                FID INTEGER PRIMARY KEY,
                STORM_TIME TIMESTAMP,
                BTID INTEGER,
                NAME TEXT,
                LAT DECIMAL(4,1),
                LONG DECIMAL(4,1),
                WIND_KTS INTEGER,
                PRESSURE INTEGER,
                CAT VARCHAR(2),
                BASIN TEXT,
                SHAPE_LENG DECIMAL(7, 6) )""")

url = 'https://dq-content.s3.amazonaws.com/251/storm_data.csv'

with requests.Session() as s:
    download = s.get(url)
    decode = download.content.decode('utf-8')
    reader = csv.reader(decode.splitlines(), delimiter=',')
    next(reader)
    for storm in reader:
        storm_update = storm[0:1] + storm[5:]
        time = split_time(storm[4])
        storm_time = datetime.datetime(int(storm[1]),int(storm[2]),int(storm[3]),int(time['hours']),int(time['minutes']),0)
        storm_update.insert(1,storm_time)
        cur.execute("INSERT INTO storm_data VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", storm_update)
    conn.commit()

cur.execute('select * from storm_data')
cur.fetchall()

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
# cur.execute('CREATE DATABASE storm_data')

def split_time(time):
    return({'hours':time[:2], 'minutes':time[2:4]})

try:
    conn = psycopg2.connect(
        host = 'sjay-rds-postgresl.cnb00fhz6hyj.ap-southeast-2.rds.amazonaws.com',
        user = 'stevenjay',
        password = 'gw7p6dy3f4',
        dbname='storm_data')
    cur = conn.cursor()
    print("Connection Established")
except:
    print("Connection Failed")

try:
    cur.execute("""DROP TABLE IF EXISTS storms""")
    conn.commit()
    print("Table dropped")
except:
    print("Table drop failed")

try:
    cur.execute("""CREATE TABLE storms (
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
                SHAPE_LENG DECIMAL(8, 6) )""")
    conn.commit()
    print("Table created")
except:
    print("Table Create Failed")

url = 'https://dq-content.s3.amazonaws.com/251/storm_data.csv'

print("Data downloaded")
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
        cur.execute("INSERT INTO storms VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", storm_update)
conn.commit()
print("Data Inserted")

cur.execute("""CREATE GROUP analysts NOLOGIN""")
cur.execute("""REVOKE ALL PRIVILEGES on storm_data FROM analysts""")
cur.execute("""GRANT INSERT ON storms TO analysts""")
cur.execute("""GRANT SELECT ON storms TO analysts""")
cur.execute("""GRANT UPDATE ON storms TO analysts""")
cur.execute("""CREATE USER scientist WITH PASSWORD 'password'""")
cur.execute("""GRANT analysts TO scientist""")

cur.execute("SELECT * FROM storms")
print(cur.fetchone()[0])

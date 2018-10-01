import io
import psycopg2
import requests

conn = psycopg2.connect(dbname='postgres', user='postgres')
cur = conn.cursor()

cur.execute('CREATE DATABASE storms')

conn = psycopg2.connect(dbname='storms', user='postgres')
cur = conn.cursor()

cur.execute("""CREATE TABLE storm_data (
                FID INTEGER PRIMARY KEY,
                STORM_TIME DATETIME,
                BTID INTEGER,
                NAME TEXT,
                LAT DECIMAL(4,1),
                LONG DECIMAL(4,1),
                WIND_KTS INTEGER,
                PRESSURE INTEGER,
                CAT VARCHAR(2),
                BASIN TEXT,
                SHAPE_LENG DECIMAL(7, 6) )""")

response = request.urlopen('https://dq-content.s3.amazonaws.com/251/storm_data.csv')
reader = csv.reader(io.TextIOWrapper(response))

for row in reader:
    new_row = row[0][]

# use following code to get csv file
#     with requests.Session() as s:
# ...     download = s.get(url)
# ...     decode = download.content.decode('utf-8')
# ...     reader = csv.reader(decode.splitlines(), delimiter=',')
# ...     mylist = list(reader)
# ...     for row in mylist:
# ...             print(row)
...

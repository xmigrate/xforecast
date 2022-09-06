from http import client
from influxdb import InfluxDBClient
from datetime import datetime

client = InfluxDBClient('192.168.1.9', 8086, 'admin', 'admin', 'telegraf')
print(client.get_list_database())
print(client.get_list_measurements())
query = 'SELECT "usage_user" FROM "autogen"."cpu" WHERE time = \'2022-09-06 10:30:00\''
value = client.query(query)
print(value)
values = list(value.get_points(measurement='cpu'))
print(values)

for elements in values:
    print(elements)

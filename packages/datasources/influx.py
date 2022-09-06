from http import client
from influxdb import InfluxDBClient
from datetime import datetime

client = InfluxDBClient('192.168.1.9', 8086, 'admin', 'admin', 'telegraf')
print(client.get_list_database())
print(client.get_list_measurements())
print(client.query('SELECT usage_idle FROM cpu'))
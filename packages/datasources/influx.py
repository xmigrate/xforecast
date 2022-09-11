from http import client
from influxdb import InfluxDBClient
from datetime import datetime
from dateutil import parser
from packages.datasources.logger import *



def get_data_from_influxdb(data_store,start_time,end_time,prev_stime,prev_etime,prom_query):
    url = data_store['url']
    port = data_store['port']
    username = data_store['user']
    password = data_store['pass']
    db_name = data_store['db_name']
    client = InfluxDBClient(url, port, username, password, db_name)

    
    
    prom_query = prom_query.replace(prev_stime,start_time)
    prom_query = prom_query.replace(prev_etime,end_time)
    query=prom_query
 
    value = client.query(query)

    value = list(value)
    if value:
        logger("Fetching data from Telegraf - Succes","warning")
    else:
        logger("Fetching data from Telegraf - Failed","warning")
    data_points = {}
    data_time = []
    data_value=[]

    for elements in value[0]:
        k=elements.keys()
        k=list(k)
        datetime_time = parser.parse(elements[k[0]])
        datetime_time = datetime_time.replace(tzinfo=None)
        data_time.append(datetime_time)
        data_value.append(elements[k[1]])
    data_points['Time'] = data_time
    data_points['y'] = data_value

    return data_points

def write_data_to_influxdb(val,tim,write_name,data_store):
    url = data_store['url']
    port = data_store['port']
    username = data_store['user']
    password = data_store['pass']
    db_name = data_store['db_name']
    measurement = data_store['measurement']
    client = InfluxDBClient(url, port, username, password, db_name)
    measurement = measurement
    json_payload=[]
    data = {}
    data['measurement'] = measurement
    data['time'] = tim
    data['fields'] = {write_name:val}
    json_payload.append(data)

    client.write_points(json_payload)
    

    

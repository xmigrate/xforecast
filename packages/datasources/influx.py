import yaml
from influxdb import InfluxDBClient
from datetime import datetime
from dateutil import parser
from yaml.loader import SafeLoader
from packages.datasources.logger import *

with open('test/mock/mockdata.yaml') as f:
    mockdata = yaml.load(f, Loader=SafeLoader)


def get_data_from_influxdb(data_store,start_time,end_time,prev_stime,prev_etime,prom_query,test=False):
    if test == False:
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
    else:
        value = mockdata['influx_results'][0]['results']['result']
        
    if value:
        logger("Fetching data from influxdb - Success","warning")
    else:
        logger("Fetching data from influxdb - Failed","warning")
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
    if test == True:
        return str(data_points)
    else:
        return data_points

def write_data_to_influxdb(val,tim,write_name,data_store,test=False):
    if test == False:
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

        if client.write_points(json_payload):
            logger("Writing data to influxdb - Success","warning")
        else:
            logger("Writing data to influxdb - Failed","warning")
    else:
        assert val == 500


        

    

    

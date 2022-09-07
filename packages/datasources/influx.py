from http import client
from influxdb import InfluxDBClient
from datetime import datetime
from dateutil import parser



def get_data_from_influxdb(metric_name,data_store,url,port,username,password,db_name,start_time,end_time,prom_query,write_back_metric):

    client = InfluxDBClient(url, port, username, password, db_name)
    #print(client.get_list_database())
    #print(client.get_list_measurements())
    metric = 'usage_user'
    measurement = 'cpu'
    query = 'SELECT "usage_user" FROM "autogen"."cpu" WHERE time >= \'2022-09-07 10:07:00\''
    value = client.query(query)
    #print(value)
    values = list(value.get_points(measurement=measurement))
    #print(values)


    data_points = {}
    data_time = []
    data_value=[]

    for elements in values:
        yourdate = parser.parse(elements['time'])
        yourdate = yourdate.replace(tzinfo=None)
        data_time.append(yourdate)
        data_value.append(elements[metric])
    data_points['Time'] = data_time
    data_points['y'] = data_value

    return data_points

def write_data_to_influxdb(val,tim,write_name,url,port,username,password,db_name):
    client = InfluxDBClient(url, port, username, password, db_name)
    measurement = 'cpu'
    json_payload=[]
    data = {}
    data['measurement'] = measurement
    data['time'] = tim
    data['fields'] = {write_name:val}
    json_payload.append(data)

    client.write_points(json_payload)

    

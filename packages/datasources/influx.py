from http import client
from influxdb import InfluxDBClient
from datetime import datetime
from dateutil import parser



def get_data_from_influxdb(metric_name,data_store,url,port,username,password,db_name,measurement,start_time,end_time,prev_stime,prev_etime,prom_query,write_back_metric):

    client = InfluxDBClient(url, port, username, password, db_name)
    #print(client.get_list_database())
    #print(client.get_list_measurements())


    # start_time = "'"+ start_time + "'"
    # end_time ="'"+ end_time + "'"

    
    #print(start_time)
    metric_name = metric_name
    measurement = measurement
    prom_query = prom_query.replace(prev_stime,start_time)
    prom_query = prom_query.replace(prev_etime,end_time)
    query=prom_query
    print(query)
    value = client.query(query)
    #print()
    values = list(value.get_points(measurement=measurement))
    #print(values)
    value = list(value)
    
    # for elements in value[0]:
    #     k=elements.keys()
    #     k=list(k)
    #     print(elements[k[0]])


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
    print(data_points)
    return data_points

def write_data_to_influxdb(val,tim,write_name,url,port,username,password,db_name,measurement):
    client = InfluxDBClient(url, port, username, password, db_name)
    measurement = measurement
    json_payload=[]
    data = {}
    data['measurement'] = measurement
    data['time'] = tim
    data['fields'] = {write_name:val}
    json_payload.append(data)

    client.write_points(json_payload)
    # print(client.write_points(json_payload))

    

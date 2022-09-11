import time
import functions
import yaml
import prometh
import datetime
import pandas as pd
from yaml.loader import SafeLoader
from collections import defaultdict
from influxdb import InfluxDBClient
from dateutil import parser


# with open('./config.yaml') as f:
#     data = yaml.load(f, Loader=SafeLoader)
# #print(data)

# metric_dict = defaultdict(list)
# for elements in data['metrics']:
#     for element in elements:
#         metric_dict[element].append(elements[element])

# metric_name = metric_dict['name']
# start_time = metric_dict['start_time']
# end_time = metric_dict['end_time']
# url = data['prometheus_url']
# prom_query = metric_dict['query']
# forecast_every = metric_dict['forecast_every']

# #print(type(forecast_every[0]))

client = InfluxDBClient('192.168.1.9', 8086, 'admin', 'admin', 'telegraf')
#print(client.get_list_database())
#print(client.get_list_measurements())
metric = 'usage_user'
measurement = 'cpu'
fieldname= ""
predicted_field = "forecast_value"
query = 'SELECT "usage_user" FROM "autogen"."cpu" WHERE time >= \'2022-09-07 6:30:00\''
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

    

dt=data_points
print(dt)
df={}
df['Time'] =  pd.to_datetime(dt['Time'], format='%d/%m/%y %H:%M:%S')
df['ds'] = df['Time']
df['y'] = dt['y']

df=pd.DataFrame(df)


#train_df = df[10:]

response = functions.fit_and_predict(df,periods=10,frequency='60s',old_model_loc=None)
print(response['ds'] ,response['yhat'])

data_to_influx_yhat = response['yhat'].to_dict()
data_to_influx_tim = response['ds'].to_dict()
json_payload=[]
data_list = []
for elements in data_to_influx_tim: 
    print( data_to_influx_yhat[elements])
    # data = {
    #     "measurement" : "cpu",
    #     "time" : data_to_influx_tim[elements],
    #     "fields" : {
    #         "forecast_value" : data_to_influx_yhat[elements]
    #     }
    # }
    data = {}
    data['measurement'] = measurement
    data['time'] = data_to_influx_tim[elements]
    data['fields'] = {predicted_field:data_to_influx_yhat[elements]}
    json_payload.append(data)

    client.write_points(json_payload)
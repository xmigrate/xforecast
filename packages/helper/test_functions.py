import time
import functions
import yaml
import prometh
import datetime
import pandas as pd
from yaml.loader import SafeLoader
from collections import defaultdict

with open('./config.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)
#print(data)

metric_dict = defaultdict(list)
for elements in data['metrics']:
    for element in elements:
        metric_dict[element].append(elements[element])

metric_name = metric_dict['name']
start_time = metric_dict['start_time']
end_time = metric_dict['end_time']
url = data['prometheus_url']
prom_query = metric_dict['query']
forecast_every = metric_dict['forecast_every']

#print(type(forecast_every[0]))



dt=prometh.get_data_from_prometheus(metric_name,prom_query, start_time, end_time, url)
print(dt)
df={}
df['Time'] =  pd.to_datetime(dt['Time'], format='%d/%m/%y %H:%M:%S')
df['ds'] = df['Time']
df['y'] = dt['y']

df=pd.DataFrame(df)


#train_df = df[10:]

response = functions.fit_and_predict(df,periods=1,frequency='60s',old_model_loc=None)
#print(response['yhat_upper'])

for keys in response:
    if keys == "yhat" or 'yhat_lower' or 'yhat_upper' or 'ds':
        print(response[keys])
        time.sleep(1)
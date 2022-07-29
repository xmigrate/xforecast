#TODO import necessary packages
import yaml
import requests
import json
import datetime
import asyncio
import time
from prometheus_pb2 import (
    TimeSeries,
    Label,
    Labels,
    Sample,
    WriteRequest
)
import calendar
import logging
import requests
import snappy
from os.path import exists
import pandas as pd
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
from yaml.loader import SafeLoader
from collections import defaultdict




def prometheus(query):
    result = json.loads(requests.get(query).text)
    value = result['data']['result']
    return value

def get_data_from_prometheus(metric_name,prom_query, start_time, end_time, url):
    data_points = {}
    data_time = []
    data_value=[]
    
    query = url+'/api/v1/query_range?query='+prom_query+'&start='+start_time+'&end='+end_time+'&step=30s'
    #print(query)
    result = prometheus(query)
    for elements in result:
        values = elements['values']
        for element in values:
            date_time=datetime.datetime.fromtimestamp(element[0])
            data_time.append(date_time)
            data_value.append(element[1]) 
    data_points['Time'] = data_time
    data_points['y'] = data_value
    #print(data_points)
    return data_points

def stan_init(m):
    """Retrieve parameters from a trained model.

    Retrieve parameters from a trained model in the format
    used to initialize a new Stan model.

    Parameters
    ----------
    m: A trained model of the Prophet class.

    Returns
    -------
    A Dictionary containing retrieved parameters of m.

    """
    res = {}
    for pname in ['k', 'm', 'sigma_obs']:
        res[pname] = m.params[pname][0][0]
    for pname in ['delta', 'beta']:
        res[pname] = m.params[pname][0]
    return res

async def fit_and_predict(metric_name,prom_query,start_time,end_time,url,periods=1000,frequency='60s',old_model_loc=None,new_model_loc='./serialized_model.json'):
    response = {}
    old_model = None
    # file_exists = exists('./'+metric_name+'.json')
    # if(file_exists):
    #     old_model_loc = './'+metric_name+'.json'
    model = None
    new_model_loc = './'+metric_name+'.json'
    data_for_training = get_data_from_prometheus(metric_name,prom_query,start_time,end_time,url)
    df={}
    df['Time'] =  pd.to_datetime(data_for_training['Time'], format='%d/%m/%y %H:%M:%S')
    df['ds'] = df['Time']
    df['y'] = data_for_training['y']
    df=pd.DataFrame(df)
    try:
        if old_model_loc != None:
            with open(old_model_loc, 'r') as fin:
                old_model = model_from_json(fin.read())  # Load model
                print(type(old_model))
            model = Prophet(seasonality_mode='multiplicative').fit(df,init=stan_init(old_model))
        else:
            model = Prophet(seasonality_mode='multiplicative').fit(df)
        with open(new_model_loc, 'w') as fout:
            fout.write(model_to_json(model))  # Save model
        future_df = model.make_future_dataframe(periods=periods, freq=frequency)
        fcst = model.predict(future_df)
        fcst = fcst[-(periods):]
        response['status'] = 'success'
        response['model_location'] = new_model_loc
        response['yhat'] = fcst['yhat']
        response['yhat_lower'] = fcst['yhat_lower']
        response['yhat_upper'] = fcst['yhat_upper']
        response['ds'] = fcst['ds']
    except Exception as e:
        print(e)
        response['status'] = 'failure'
    return(response)

def dt2ts(dt):
    """Converts a datetime object to UTC timestamp
    naive datetime will be considered UTC.
    """
    return calendar.timegm(dt.utctimetuple())

def write_to_prometheus(val,tim):

    write_request = WriteRequest()

    series = write_request.timeseries.add()

    # name label always required
    label = series.labels.add()
    label.name = "__name__"
    label.value = "custom_nameer"
    
    # as many labels you like
    # label = series.labels.add()
    # label.name = "ssl_cipher"
    # label.value = "some_value"

    sample = series.samples.add()
    sample.value = val # your count?
    sample.timestamp = int(tim.timestamp()) * 1000
    print(sample.timestamp)
    print(dt2ts(datetime.datetime.utcnow()) * 1000)
    


    uncompressed = write_request.SerializeToString()
    compressed = snappy.compress(uncompressed)

    url = "http://localhost:9000/api/v1/write"
    headers = {
        "Content-Encoding": "snappy",
        "Content-Type": "application/x-protobuf",
        "X-Prometheus-Remote-Write-Version": "0.1.0",
        "User-Agent": "metrics-worker"
    }
    try:
        response = requests.post(url, headers=headers, data=compressed)
        print(response)
    except Exception as e:
        print(e)
    

async def call_to_all(metrics,data):
    metric_name = metrics['name']
    start_time = metrics['start_time']
    end_time = metrics['end_time']
    url = data
    prom_query = metrics['query']
    forecast_every = metrics['forecast_every']
    

    for i in range(len(metric_name)):
        file_exists = exists('./'+metric_name[i]+'.json')
        old_model_loc=None
        # if(file_exists):
        #     old_model_loc = './'+metric_name[i]+'.json'
        a=asyncio.gather(fit_and_predict(metric_name[i],prom_query[i],start_time[i],end_time[i],url,periods=1000,frequency='60s',old_model_loc=old_model_loc))
        while not a.done():
            await asyncio.sleep(1)
            try:
                result = a.result()
                #print(result[0]['ds'])
            except asyncio.CancelledError:
                print("Someone cancelled")
            except Exception as e:
                print(f"Some error: {e}")
                await call_to_all()
    return result


async def main():
    #TODO read the config file and assign to the variables
    #Check datastore type, if prometheus get it from get_data_from_promethues(metric_name, start_time, end_time, url)
    #Check if there's a trained model available for the given metric, else do the training also check the retrain flag in the config of each metric
    #Give predictions back to the prometheus if trained model is available locally
    with open('./config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
    #print(data)

    metric_dict = defaultdict(list)
    for elements in data['metrics']:
        for element in elements:
            metric_dict[element].append(elements[element])
    
    
    result1=await call_to_all(metric_dict,data['prometheus_url'])
    data_to_prom_val = result1[0]['yhat'].to_dict()
    data_to_prom_tim = result1[0]['ds'].to_dict()
    for elements in data_to_prom_val:
        await asyncio.sleep(15)
        write_to_prometheus(data_to_prom_val[elements],data_to_prom_tim[elements])
        
    
    while True:
        #get status of the async functions and restart failed ones
        pass

asyncio.run(main())

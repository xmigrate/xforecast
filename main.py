#TODO import necessary packages
import yaml
import requests
import json
import datetime
import asyncio
import time
from packages.datasources.prometheus_pb2 import (
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




def prometheus(query):
    """Gets data from prometheus using the http api.

    Parameters
    ----------
    query: proemtheus query for the metric

    Returns
    -------
    values: Result from prometheus
    """

    result = json.loads(requests.get(query).text)
    value = result['data']['result']
    return value

def get_data_from_prometheus(prom_query, start_time, end_time, url):
    """Get the required data points by querying prometheus.

    Parameters
    ----------
    prom_query: Prometheus query
    start_time : start time for the prometheus query
    end_time : end time for the prometheus query
    url : Prometheus url

    Returns
    -------
    data_points: A dictionary of lists containing time and values that are returned from prometheus
    
    """


    data_points = {}
    data_time = []
    data_value=[]
    
    query = url+'/api/v1/query_range?query='+prom_query+'&start='+str(start_time)+'&end='+str(end_time)+'&step=30s'
    #print(query)
    result = prometheus(query)
    for elements in result:
        values = elements['values']
        for element in values:
            date_time=datetime.datetime.utcfromtimestamp(element[0])
            #print(date_time)
            data_time.append(date_time)
            data_value.append(element[1]) 
    data_points['Time'] = data_time
    data_points['y'] = data_value
    #print(data_points)
    return data_points

def dt2ts(dt):
    """Converts a datetime object to UTC timestamp
    naive datetime will be considered UTC.
    """
    return calendar.timegm(dt.utctimetuple())

def write_to_prometheus(val,tim,write_name):
    """Write the predicted data to prometheus.
    
    Parameters
    ----------
    val: Value to be written
    tim: Which time the value should be written
    write_name: Custom metric name to be written

    """

    write_request = WriteRequest()

    series = write_request.timeseries.add()

    # name label always required
    label = series.labels.add()
    label.name = "__name__"
    label.value = write_name
    
    # as many labels you like
    # label = series.labels.add()
    # label.name = "ssl_cipher"
    # label.value = "some_value"

    sample = series.samples.add()
    sample.value = val # your count?
    dtl = int(tim.timestamp())
    # print(dtl)
    # dtt = datetime.datetime.fromtimestamp(dtl)
    # print(dtt)
    sample.timestamp = dtl *1000
    
    print(sample.timestamp)
    


    uncompressed = write_request.SerializeToString()
    compressed = snappy.compress(uncompressed)

    url = "http://localhost:9090/api/v1/write"
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

async def fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,periods=1,frequency='60s',old_model_loc=None,new_model_loc='./serialized_model.json'):
    """Predicts the values according to the data points recieved 
    
    Parameters
    ----------
    metric_name : metric name in prometheus
    start_time : start time for the prometheus query
    end_time : end time for the prometheus query
    url : Prometheus url
    prom_query = Prometheus query
    write_back_metric = name of the predicted/written metric
    periods = no of data points predicted
    frequency =  
    old_model_location = location of the trained model
    new_model_location = location where the newly trained model should be saved

    """

    response = {}
    old_model = None
    model = None
    new_model_loc = './packages/models/'+metric_name+'.json'
    data_for_training = get_data_from_prometheus(prom_query,start_time,end_time,url)
    df={}
    df['Time'] =  pd.to_datetime(data_for_training['Time'], format='%d/%m/%y %H:%M:%S')
    df['ds'] = df['Time']
    df['y'] = data_for_training['y']
    df=pd.DataFrame(df)
    #print(df.shape)
    #print(df.head())
    try:
        if old_model_loc != None:
            with open(old_model_loc, 'r') as fin:
                old_model = model_from_json(fin.read())  # Load model
                #print(type(old_model))
            model = Prophet(seasonality_mode='multiplicative').fit(df,init=stan_init(old_model))
        else:
            model = Prophet(seasonality_mode='multiplicative').fit(df)
        if old_model_loc == None:
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
    #print(response)
    data_to_prom_yhatlower = response['yhat_lower'].to_dict()
    data_to_prom_yhatupper = response['yhat_upper'].to_dict()
    data_to_prom_yhat = response['yhat'].to_dict()
    data_to_prom_tim = response['ds'].to_dict()
    for elements in data_to_prom_tim:
        write_to_prometheus(data_to_prom_yhat[elements],data_to_prom_tim[elements],write_back_metric+'_yhat')
        write_to_prometheus(data_to_prom_yhatlower[elements],data_to_prom_tim[elements],write_back_metric+'_yhat_lower')
        write_to_prometheus(data_to_prom_yhatupper[elements],data_to_prom_tim[elements],write_back_metric+'_yhat_upper')
    


async def main():
    """Reads the configuration file and creates a metric list"""


    with open('./config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
    #print(data)

    metric_list = []
    for metric in data['metrics']:
        metric_list.append(metric)
    url =data['prometheus_url']
    await forecast(metric_list,url)
        
async def predict_every(metric_name,start_time,end_time,url,prom_query,write_back_metric,forecast_every,forecast_basedon):
    """Calls fit_and_predict function at the required intervals

    Parameters
    ----------
    metric_name : metric name in prometheus
    start_time : start time for the prometheus query
    end_time : end time for the prometheus query
    url : Prometheus url
    prom_query = Prometheus query
    write_back_metric = name of the predicted/written metric
    forecast_every: At what interval the app do the predictions
    forecast_basedon: Forecast based on past how many data points
    
    """
    n=0
    while True:
        periods=(forecast_every/60)
        periods = int(periods)
        file_exists = exists('./packages/models/'+metric_name+'.json')
        if(file_exists):
            old_model_loc = './packages/models/'+metric_name+'.json'
        if n>0:
            #print("2nd")
            end_time = int(time.time())
            start_time = end_time - (forecast_basedon)
            await fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,periods=periods,frequency='60s',old_model_loc=old_model_loc)
        else:
            #print("og")
            await fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,periods=periods,frequency='60s',old_model_loc=None)
        n+=1
        await asyncio.sleep((forecast_every))


async def forecast(metric_list,url): 
    """Creates a tuple of functions and calls them using asyncio.gather. 
    calls recursively if there is an exception.

    parameters
    ----------
    metric_list: A list of dictionaries containing metric details.
    url : Prometheus Url.

    """
    while True:
        #get status of the async functions and restart failed ones
        async_params = []
        for metric in metric_list:
            async_params.append(predict_every(metric['name'],metric['start_time'],metric['end_time'],url,metric['query'],metric['write_back_metric'],metric['forecast_every'],metric['forecast_basedon']))
        async_params = tuple(async_params)
        g = asyncio.gather(*async_params)
        while not g.done():
            await asyncio.sleep(1)
        try:
            result = g.result()
        except asyncio.CancelledError:
            print("Someone cancelled")
            break
        except Exception as e:
            print(f"Some error: {e}")
            break
         
    await forecast(metric_list,url)
    

asyncio.run(main())
import yaml
import asyncio
import time
from datetime import datetime,timedelta
from packages.datasources.logger import *
from packages.helper.fit_and_predict import *
from os.path import exists
from yaml.loader import SafeLoader

async def main():
    """Reads the configuration file and creates a metric list"""


    with open('./config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
    #print(data)
    logger("Reading configuration","warning")

    metric_list = []
    for metric in data['metrics']:
        metric_list.append(metric)
    await forecast(metric_list)
        
async def predict_every(metric_name,data_store,start_time,end_time,prom_query,write_back_metric,forecast_every,forecast_basedon):
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
    prev_stime = start_time
    prev_etime = end_time
    while True:
        periods=(forecast_every/60)
        periods = int(periods)
        
        print(periods)
        file_exists = exists('./packages/models/'+metric_name+'.json')
        if(file_exists):
            old_model_loc = './packages/models/'+metric_name+'.json'
        if n>0:
            #print("2nd")
            if data_store['name'] == 'prometheus':
                end_time = int(time.time())
                start_time = end_time - (forecast_basedon)
            elif data_store['name'] == 'influxdb':
                end_time = datetime.utcnow()
                end_time = end_time.replace(second=0)
                t = int(forecast_basedon/60)
                start_time = end_time - timedelta(minutes=t)
                start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

            await fit_and_predict(metric_name,data_store,start_time,end_time,prom_query,write_back_metric,prev_stime,prev_etime,periods=periods,frequency='60s',old_model_loc=old_model_loc)
        else:
            #print("og")
            await fit_and_predict(metric_name,data_store,start_time,end_time,prom_query,write_back_metric,prev_stime,prev_etime,periods=periods,frequency='60s',old_model_loc=None)

        n+=1
        await asyncio.sleep((forecast_every))


async def forecast(metric_list): 
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
            async_params.append(predict_every(metric['name'],metric['data_store'],metric['start_time'],metric['end_time'],metric['query'],metric['write_back_metric'],metric['forecast_every'],metric['forecast_basedon']))
        async_params = tuple(async_params)
        g = asyncio.gather(*async_params)
        while not g.done():
            await asyncio.sleep(1)
        try:
            result = g.result()
        except asyncio.CancelledError:
            print("Someone cancelled")
            msg="Someone cancelled"
            logger(str(msg),"warning")
            break
        except Exception as e:
            print(f"Some error: {e}")
            logger("Some error"+str(e),"error")
            break
         
    await forecast(metric_list)
    

asyncio.run(main())
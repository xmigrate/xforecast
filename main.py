import yaml
import asyncio
import time
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
    url =data['prometheus_url']
    await forecast(metric_list,url)
        
async def predict_every(metric_name,start_time,end_time,url,prom_query,write_back_metric,forecast_every,forecast_basedon,model):
    """Calls fit_and_predict function at the required intervals

    Parameters
    ----------
    metric_name : metric name in prometheus
    start_time : start time for the prometheus query
    end_time : end time for the prometheus query
    url : prometheus url
    prom_query = prometheus query
    write_back_metric = name of the predicted/written metric
    forecast_every: at what interval the app does the predictions
    forecast_basedon: forecast based on past how many data points
    model: dictionary containing the model name and its hyperparameters for tuning
    
    """
    if model['model_name'] == 'prophet':
        n=0
        while True:
            periods=(forecast_every/60)
            periods = int(periods)
            print(periods)
            file_exists = exists('./packages/models/'+metric_name+'.json')
            if(file_exists):
                old_model_loc = './packages/models/'+metric_name+'.json'
            if n>0:
                #print("2nd")
                end_time = int(time.time())
                start_time = end_time - (forecast_basedon)
                await fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,model,periods=periods,frequency='60s',old_model_loc=old_model_loc)
            else:
                #print("og")
                await fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,model,periods=periods,frequency='60s',old_model_loc=None)
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
            async_params.append(predict_every(metric['name'],metric['start_time'],metric['end_time'],url,metric['query'],metric['write_back_metric'],metric['forecast_every'],metric['forecast_basedon'],metric['models']))
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
         
    await forecast(metric_list,url)
    

asyncio.run(main())
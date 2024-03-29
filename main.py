import yaml
import asyncio
import time
from datetime import datetime,timedelta,timezone
from packages.datasources.logger import *
from packages.helper.fit_and_predict import *
from os.path import exists
from yaml.loader import SafeLoader

async def main():
    """Reads the configuration file and creates a metric list"""


    with open('./config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
    #print(data)
    logger("Reading configuration","info")

    metric_list = []
    for metric in data['metrics']:
        metric_list.append(metric)
    await forecast(metric_list)
        
async def predict_every(metric_name,data_store,start_time,end_time,db_query,write_back_metric,forecast_every,forecast_basedon,model):
    """Calls fit_and_predict function at the required intervals

    Parameters
    ----------
    metric_name : metric name in database
    data_store : dictionary containing details of the database used for query
    start_time : start time for the database query
    end_time : end time for the database query
    db_query : database query
    write_back_metric : name of the predicted/written metric
    forecast_every: at what interval the app does the predictions
    forecast_basedon: forecast based on past how many data points
    model: dictionary containing the model name and its hyperparameters for tuning
    
    """
    if model['model_name'] == 'prophet':
        n=0
        prev_stime = start_time
        prev_etime = end_time
        while True:
            periods=(forecast_every/60)
            periods = int(periods)
            #print(periods)
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
                await fit_and_predict(metric_name,data_store,start_time,end_time,db_query,write_back_metric,model,prev_stime,prev_etime,periods=periods,frequency='60s',old_model_loc=old_model_loc)
            else:
                #print("og")
                if data_store['name'] == 'prometheus':
                    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                    start_time = int(start_time.replace(tzinfo=timezone.utc).timestamp())
                    end_time = int(end_time.replace(tzinfo=timezone.utc).timestamp())
                await fit_and_predict(metric_name,data_store,start_time,end_time,db_query,write_back_metric,model,prev_stime,prev_etime,periods=periods,frequency='60s',old_model_loc=None)
            n+=1
            await asyncio.sleep((forecast_every))

async def forecast(metric_list): 
    """Creates a tuple of functions and calls them using asyncio.gather. 
    calls recursively if there is an exception.

    parameters
    ----------
    metric_list: A list of dictionaries containing metric details

    """
    while True:
        #get status of the async functions and restart failed ones
        async_params = []
        for metric in metric_list:
            async_params.append(predict_every(metric['name'],metric['data_store'],metric['start_time'],metric['end_time'],metric['query'],metric['write_back_metric'],metric['forecast_every'],metric['forecast_basedon'],metric['models']))
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
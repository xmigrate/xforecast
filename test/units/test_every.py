from os.path import exists
import asyncio,time

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
        print(periods)
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

async def fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,periods=10,frequency='60s',old_model_loc='./somewhere'):
    print("hi")
from os.path import exists
import pandas as pd
import pytest,json,datetime,requests
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
#from test_sample import get_data_from_prometheus



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
    status=result['status']
    # if value:
    #     logger("Fetching data from prometheus - Succes","warning")
    # else:
    #     logger("Fetching data from prometheus - Failed","warning")
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

    #logger("Fetching data from prometheus","warning")
    data_points = {}
    data_time = []
    data_value=[]
    
    query = url+'/api/v1/query_range?query='+prom_query+'&start='+str(start_time)+'&end='+str(end_time)+'&step=15s'
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
    print(data_points)
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

async def fit_and_predict(metric_name,start_time,end_time,url,prom_query,periods=1,frequency='60s',old_model_loc=None,new_model_loc='./serialized_model.json'):
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
    new_model_loc = './'+metric_name+'.json'
    
    url="http://localhost:9000"
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
            # logger("Retraining ML model","warning")
            model = Prophet(seasonality_mode='multiplicative', daily_seasonality=True,yearly_seasonality=True, weekly_seasonality=True).fit(df,init=stan_init(old_model))
        else:
            # logger("Training ML model","warning")
            model = Prophet(seasonality_mode='multiplicative',daily_seasonality=True,yearly_seasonality=True, weekly_seasonality=True).fit(df)
        #if old_model_loc == None:
        with open(new_model_loc, 'w') as fout:
            fout.write(model_to_json(model))  # Save model
        future_df = model.make_future_dataframe(periods=periods, freq=frequency)
        fcst = model.predict(future_df)
        fcst = fcst[-(periods):]
        # logger("Predicting future data points","warning")
        response['status'] = 'success'
        response['model_location'] = new_model_loc
        response['yhat'] = fcst['yhat']
        response['yhat_lower'] = fcst['yhat_lower']
        response['yhat_upper'] = fcst['yhat_upper']
        response['ds'] = fcst['ds']
        assert response['status'] != 'success'
    except Exception as e:
        print(e)
        response['status'] = 'failure'
        # logger(str(e),"error")
    #print(response)
    data_to_prom_yhatlower = response['yhat_lower'].to_dict()
    data_to_prom_yhatupper = response['yhat_upper'].to_dict()
    data_to_prom_yhat = response['yhat'].to_dict()
    data_to_prom_tim = response['ds'].to_dict()
    # for elements in data_to_prom_tim:
    #     write_to_prometheus(data_to_prom_yhat[elements],data_to_prom_tim[elements],write_back_metric+'_yhat')
    #     write_to_prometheus(data_to_prom_yhatlower[elements],data_to_prom_tim[elements],write_back_metric+'_yhat_lower')
    #     write_to_prometheus(data_to_prom_yhatupper[elements],data_to_prom_tim[elements],write_back_metric+'_yhat_upper')

@pytest.mark.asyncio
async def test_fit_predict():
    metric_name = "name"
    prom_query = "windows_os_physical_memory_free_bytes"
    start_time = '2022-08-08T09:27:00.000Z'
    end_time = '2022-08-08T09:28:00.000Z'
    url="http://localhost:9000"
    await fit_and_predict(metric_name,start_time,end_time,url,prom_query,periods=10,frequency="60s",old_model_loc=None,new_model_loc=None)

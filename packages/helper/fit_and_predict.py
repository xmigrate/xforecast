import pandas as pd
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
from packages.datasources.prometheus import *


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

async def fit_and_predict(metric_name,start_time,end_time,url,prom_query,write_back_metric,models,periods=1,frequency='60s',old_model_loc=None,new_model_loc='./serialized_model.json'):
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
    params = models["hyperparameters"]
    df=pd.DataFrame(df)
    #print(df.shape)
    #print(df.head())
    try:
        
        if old_model_loc != None:
            with open(old_model_loc, 'r') as fin:
                old_model = model_from_json(fin.read())  # Load model
                
            logger("Retraining ML model","warning")
            model = Prophet(changepoint_prior_scale=params["changepoint_prior_scale"],seasonality_prior_scale=params["seasonality_prior_scale"],holidays_prior_scale=params["holidays_prior_scale"],changepoint_range=params["changepoint_range"],seasonality_mode=params["seasonality_mode"],).fit(df,init=stan_init(old_model))
        else:
            logger("Training ML model","warning")
            model = Prophet(changepoint_prior_scale=params["changepoint_prior_scale"],seasonality_prior_scale=params["seasonality_prior_scale"],holidays_prior_scale=params["holidays_prior_scale"],changepoint_range=params["changepoint_range"],seasonality_mode=params["seasonality_mode"]).fit(df)
        #if old_model_loc == None:
        with open(new_model_loc, 'w') as fout:
            fout.write(model_to_json(model))  # Save model
        future_df = model.make_future_dataframe(periods=periods, freq=frequency)
        fcst = model.predict(future_df)
        fcst = fcst[-(periods):]
        logger("Predicting future data points","warning")
        response['status'] = 'success'
        response['model_location'] = new_model_loc
        response['yhat'] = fcst['yhat']
        response['yhat_lower'] = fcst['yhat_lower']
        response['yhat_upper'] = fcst['yhat_upper']
        response['ds'] = fcst['ds']
    except Exception as e:
        print(e)
        response['status'] = 'failure'
        logger(str(e),"error")
    #print(response)
    data_to_prom_yhatlower = response['yhat_lower'].to_dict()
    data_to_prom_yhatupper = response['yhat_upper'].to_dict()
    data_to_prom_yhat = response['yhat'].to_dict()
    data_to_prom_tim = response['ds'].to_dict()
    for elements in data_to_prom_tim:
        write_to_prometheus(data_to_prom_yhat[elements],data_to_prom_tim[elements],write_back_metric+'_yhat',url)
        write_to_prometheus(data_to_prom_yhatlower[elements],data_to_prom_tim[elements],write_back_metric+'_yhat_lower',url)
        write_to_prometheus(data_to_prom_yhatupper[elements],data_to_prom_tim[elements],write_back_metric+'_yhat_upper',url)
    
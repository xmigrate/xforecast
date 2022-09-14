import pandas as pd
import json
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
from packages.datasources.prometheus import *
from packages.datasources.influx import *


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

async def fit_and_predict(metric_name,data_store,start_time,end_time,db_query,write_back_metric,model,prev_stime,prev_etime,periods=1,frequency='60s',old_model_loc=None,new_model_loc='./serialized_model.json',test=False):
    """Predicts the values according to the data points recieved 
    
    Parameters
    ----------
    metric_name : metric name in prometheus
    start_time : start time for the prometheus query
    end_time : end time for the prometheus query
    prom_query = Prometheus query
    write_back_metric = name of the predicted/written metric
    model: dictionary containing the model name and its hyperparameters for tuning
    periods = number of data points predicted
    frequency =  
    old_model_location = location of the trained model
    new_model_location = location where the newly trained model should be saved

    """

    response = {}
    old_model = None
    prophet_model = None
    new_model_loc = './packages/models/'+metric_name+'.json'
    
    if test == False:
        if data_store['name'] == 'prometheus':
            data_for_training = get_data_from_prometheus(db_query,start_time,end_time,data_store['url'])
        elif data_store['name'] == "influxdb":
            data_for_training = get_data_from_influxdb(data_store,start_time,end_time,prev_stime,prev_etime,db_query)
    else:
        data_for_training = {"Time": [datetime(2023, 9, 12, 8, 53), datetime(2022, 9, 12, 8, 53, 10), datetime(2022, 9, 12, 8, 53, 20), datetime(2022, 9, 12, 8, 53, 30), datetime(2022, 9, 12, 8, 53, 40), datetime(2022, 9, 12, 8, 53, 50), datetime(2022, 9, 12, 8, 54)], "y": [50.87687511613649, 50.57760243944724, 50.50485283113489, 50.664869957894595, 50.527145382764374, 50.48463651916247, 50.54480966540953]}
        
        
    df={} 
    df['Time'] =  pd.to_datetime(data_for_training['Time'], format='%d/%m/%y %H:%M:%S')
    df['ds'] = df['Time']
    df['y'] = data_for_training['y']

    params = model["hyperparameters"]

    df=pd.DataFrame(df)

    #print(df.shape)
    #print(df.head())
    try:
        
        if old_model_loc != None:
            with open(old_model_loc, 'r') as fin:
                old_model = model_from_json(fin.read())  # Load model
                
            logger("Retraining ML model","warning")
            prophet_model = Prophet(changepoint_prior_scale=params["changepoint_prior_scale"],seasonality_prior_scale=params["seasonality_prior_scale"],holidays_prior_scale=params["holidays_prior_scale"],changepoint_range=params["changepoint_range"],seasonality_mode=params["seasonality_mode"],).fit(df,init=stan_init(old_model))
        else:
            logger("Training ML model","warning")
            prophet_model = Prophet(changepoint_prior_scale=params["changepoint_prior_scale"],seasonality_prior_scale=params["seasonality_prior_scale"],holidays_prior_scale=params["holidays_prior_scale"],changepoint_range=params["changepoint_range"],seasonality_mode=params["seasonality_mode"]).fit(df)
        #if old_model_loc == None:
        with open(new_model_loc, 'w') as fout:
            fout.write(model_to_json(prophet_model))  # Save model
        future_df = prophet_model.make_future_dataframe(periods=periods, freq=frequency)
        fcst = prophet_model.predict(future_df)
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


    data_to_write_yhatlower = response['yhat_lower'].to_dict()
    data_to_write_yhatupper = response['yhat_upper'].to_dict()
    data_to_write_yhat = response['yhat'].to_dict()
    data_to_write_tim = response['ds'].to_dict()
    if test == False:
        for elements in data_to_write_tim:
            if data_store['name'] == "prometheus":
                write_to_prometheus(data_to_write_yhat[elements],data_to_write_tim[elements],write_back_metric+'_yhat',data_store['url'])
                write_to_prometheus(data_to_write_yhatlower[elements],data_to_write_tim[elements],write_back_metric+'_yhat_lower',data_store['url'])
                write_to_prometheus(data_to_write_yhatupper[elements],data_to_write_tim[elements],write_back_metric+'_yhat_upper',data_store['url'])
            elif data_store['name'] == "influxdb":
                write_data_to_influxdb(data_to_write_yhat[elements],data_to_write_tim[elements],write_back_metric+'_yhat',data_store)
                write_data_to_influxdb(data_to_write_yhatlower[elements],data_to_write_tim[elements],write_back_metric+'_yhat_lower',data_store)
                write_data_to_influxdb(data_to_write_yhatupper[elements],data_to_write_tim[elements],write_back_metric+'_yhat_upper',data_store)
    else:
        assert data_to_write_yhat == {7: 50.824059424195525}
    
import pandas as pd
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json

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

def fit_and_predict(df, periods=1000,frequency='60s',old_model_loc=None,new_model_loc='./serialized_model.json'):
    response = {}
    old_model = None
    model = None
    new_model_loc = new_model_loc
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


from packages.helper.fit_and_predict import *
import pytest

@pytest.mark.asyncio
async def test_fit_and_predict():
    metric_name = "mockname"
    data_store = "mockstore"
    start_time = '2022-09-12 08:53:00'
    end_time = '2022-09-12 08:54:00'
    prev_stime = '2022-09-12 08:50:00'
    prev_etime = '2022-09-12 08:51:00'
    prom_query = "mockquery"
    write_back_metric = "mockmetric"
    model = {'hyperparameters': {'changepoint_prior_scale':0.05, 'seasonality_prior_scale':10, 'holidays_prior_scale':10, 'changepoint_range':0.8, 'seasonality_mode':'additive'}}
    r = await fit_and_predict(metric_name,data_store,start_time,end_time,prom_query,write_back_metric,model,prev_stime,prev_etime,periods=1,frequency='60s',old_model_loc=None,test=True)
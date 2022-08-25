import yaml,pytest,asyncio
from yaml.loader import SafeLoader

@pytest.mark.asyncio
async def test_main():
    """Reads the configuration file and creates a metric list"""


    with open('./config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
    #print(data)
    #logger("Reading configuration","warning")

    metric_list = []
    for metric in data['metrics']:
        metric_list.append(metric)
    url =data['prometheus_url']
    #await forecast(metric_list,url)
    assert 'http://host.docker.internal:9000' in url



@pytest.mark.asyncio
async def test_forecast(metric_list = [{'name':'mockname','start_time':1660819843,'end_time':1660823482,'query':'mockquery','forecast_every':60,'forecast_basedon':3600,'write_back_metric':'forecastmetric'}],url = "http://localhost:9000"): 
    """Creates a tuple of functions and calls them using asyncio.gather. 
    calls recursively if there is an exception.

    parameters
    ----------
    metric_list: A list of dictionaries containing metric details.
    url : Prometheus Url.

    """
    
    #get status of the async functions and restart failed ones
    async_params = []
    for metric in metric_list:
        async_params.append(predict_every(metric['name'],metric['start_time'],metric['end_time'],url,metric['query'],metric['write_back_metric'],metric['forecast_every'],metric['forecast_basedon']))
    assert len(async_params) > 0
    async_params = tuple(async_params)
    g = asyncio.gather(*async_params)
    while not g.done():
        await asyncio.sleep(1)
    try:
        result = g.result()
    except asyncio.CancelledError:
        print("Someone cancelled")
        msg="Someone cancelled"
        #logger(str(msg),"warning")
        #break
    except Exception as e:
        print(f"Some error: {e}")
        #logger("Some error"+str(e),"error")
        #break
        
#await forecast(metric_list,url)
@pytest.mark.asyncio
async def predict_every(a,b,c,d,e,f,g,h):
    print(a)























# @pytest.mark.asyncio
# async def test_an_async_function():
#     await main()
#@pytest.mark.asyncio
# def test_forecast_():
#     metric = [{'name':'mockname','start_time':'time','end_time':'timme','query':'mockquery','forecast_every':'10','forecast_basedon':'10','write_back_metric':'forecastmetric'}]
#     urll = "http://localhost:9000"
#     asyncio.run(test_forecast(metric,urll))
# asyncio.run(test_forecast_())
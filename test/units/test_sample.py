import yaml,datetime,pytest
import json,requests,calendar,snappy
from yaml.loader import SafeLoader
from prometheus_pb2 import (
    TimeSeries,
    Label,
    Labels,
    Sample,
    WriteRequest
)
with open('test/mock/mockdata.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)
def prometheus(query):
    """Gets data from prometheus using the http api.

    Parameters
    ----------
    query: proemtheus query for the metric

    Returns
    -------
    values: Result from prometheus
    """
    assert query == "http://localhost:9000/api/v1/query_range?query=windows_os_physical_memory_free_bytes&start=2022-08-08T09:27:00.000Z&end=2022-08-08T09:28:00.000Z&step=15s"
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
    assert url =="http://localhost:9000"
    query = url+'/api/v1/query_range?query='+prom_query+'&start='+str(start_time)+'&end='+str(end_time)+'&step=15s'
    #print(query)
    result = data[0]['result']
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
    #assert data_points == data[1]['result']
    return data_points

def dt2ts(dt):
    """Converts a datetime object to UTC timestamp
    naive datetime will be considered UTC.
    """
    return calendar.timegm(dt.utctimetuple())

def write_to_prometheus(val,tim,write_name):
    """Write the predicted data to prometheus.
    
    Parameters
    ----------
    val: Value to be written
    tim: Which time the value should be written
    write_name: Custom metric name to be written

    """
    # logger("Writing data to prometheus","warning")
    write_request = WriteRequest()

    series = write_request.timeseries.add()

    # name label always required
    label = series.labels.add()
    label.name = "__name__"
    label.value = write_name
    
    # as many labels you like
    # label = series.labels.add()
    # label.name = "ssl_cipher"
    # label.value = "some_value"

    sample = series.samples.add()
    sample.value = val # your count?
    #dtl = int(tim.timestamp())
    # print(dtl)
    # dtt = datetime.datetime.fromtimestamp(dtl)
    # print(dtt)
    sample.timestamp = tim *1000

    assert sample.timestamp == 1660887343000
    
    print(sample.timestamp)
    

    
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




def test_answer():
    query = "http://localhost:9000/api/v1/query_range?query=windows_os_physical_memory_free_bytes&start=2022-08-08T09:27:00.000Z&end=2022-08-08T09:28:00.000Z&step=15s"
def test_get_data():
    prom_query = "windows_os_physical_memory_free_bytes"
    start = '2022-08-08T09:27:00.000Z'
    end = '2022-08-08T09:28:00.000Z'
    url="http://localhost:9000"
    r = get_data_from_prometheus(prom_query,start,end,url)
    assert r != data[1]['result']
def test_write_to():
    write_name = "forecast_prom"
    tim = 1660887343
    val = 500
    write_to_prometheus(val,tim,write_name)

#get_data_from_prometheus("windows_os_physical_memory_free_bytes","2022-08-08T09:27:00.000Z","2022-08-08T09:28:00.000Z","http://localhost:9000")
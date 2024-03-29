from time import strftime
import requests
import json,yaml
import datetime
import snappy
import calendar
from yaml.loader import SafeLoader
from packages.datasources.logger import *
from packages.datasources.prometheus_pb2 import (
    TimeSeries,
    Label,
    Labels,
    Sample,
    WriteRequest
)

with open('test/mock/mockdata.yaml') as f:
    mockdata = yaml.load(f, Loader=SafeLoader)

def prometheus(query,test=False):
    """Gets data from prometheus using the http api.

    Parameters
    ----------
    query: proemtheus query for the metric

    Returns
    -------
    values: Result from prometheus

    """


    if test == True:
        result = mockdata['prom_results'][0]['results']['result']
    else:
        result = json.loads(requests.get(query).text)

    value = result['data']['result']
    status=result['status']
    if value:
        logger("Fetching data from prometheus - Success","info")
    else:
        logger("Fetching data from prometheus - Failed","error")
    return value

def get_data_from_prometheus(db_query, start_time, end_time, url,test=False):
    """Get the required data points by querying prometheus.

    Parameters
    ----------
    db_query: database query
    start_time : start time for the database query
    end_time : end time for the database query
    url : Prometheus url

    Returns
    -------
    data_points: A dictionary of lists containing time and values that are returned from prometheus
    
    """

    data_points = {}
    data_time = []
    data_value=[]
    query = url+'/api/v1/query_range?query='+db_query+'&start='+str(start_time)+'&end='+str(end_time)+'&step=15s'
    if test == True:
        result = mockdata['getdata_results'][0]['results']['result']
    else:
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
    if test == True:
        return str(data_points)
    else:
        return data_points

def dt2ts(dt):
    """Converts a datetime object to UTC timestamp
    naive datetime will be considered UTC.
    """
    return calendar.timegm(dt.utctimetuple())

def write_to_prometheus(val,tim,write_name,prom_url,test=False):
    """Write the predicted data to prometheus.
    
    Parameters
    ----------
    val: Value to be written
    tim: Which time the value should be written
    write_name: Custom metric name to be written
    
    """

    
      

    write_request = WriteRequest()

    series = write_request.timeseries.add()

    # name label always required
    label = series.labels.add()
    label.name = "__name__"
    label.value = write_name
    

    sample = series.samples.add()
    sample.value = val # your count?
    dtl = int(tim.timestamp())
    sample.timestamp = dtl *1000

    #print(sample.timestamp)
    


    uncompressed = write_request.SerializeToString()
    compressed = snappy.compress(uncompressed)
    
    url = prom_url+"/api/v1/write"
    headers = {
        "Content-Encoding": "snappy",
        "Content-Type": "application/x-protobuf",
        "X-Prometheus-Remote-Write-Version": "0.1.0",
        "User-Agent": "metrics-worker"
    }
    if test == False:
        try:
            response = requests.post(url, headers=headers, data=compressed)
            #print(response)
            response = str(response)
            if response == '<Response [204]>':
                #print("writing failed")
                logger("writing data to prometheus - Success","info")
            else:
                logger("writing data to prometheus - Failed","error")

        except Exception as e:
            print(e)
            logger(str(e),"error")
    else:
        assert val == 5000
from time import strftime
import yaml
import requests
import json
import datetime
import asyncio
from yaml.loader import SafeLoader
from collections import defaultdict



def prometheus(query):
    result = json.loads(requests.get(query).text)
    value = result['data']['result']
    return value

def get_data_from_prometheus(metric_name,prom_query, start_time, end_time, url):
    data_points = {}
    data_time=[]
    data_value=[]
    for i in range(len(metric_name)):
        if metric_name[i]:
            query = url+'/api/v1/query_range?query='+prom_query[i]+'&start='+start_time[i]+'&end='+end_time[i]+'&step=15s'
            #print(query)
            result = prometheus(query)
            for elements in result:
                values = elements['values']
                for element in values:
                    #print(element[0])
                    date_time=datetime.datetime.fromtimestamp(element[0])
                    #date_time = date_time,strftime('%y/%m/%d %H:%S')
                    #print(date_time)
                    data_time.append(date_time)
                    data_value.append(element[1]) 
    data_points['Time'] = data_time
    data_points['y'] = data_value
    return data_points

def train_model():
    pass

async def predict_datapoints(forecast_every,metric_name):
     while True:
        #TODO If trained model available, else break
        #Get the past data points and pass that to the model for prediction
        #Get the predictions and store that to prometheus data store
        #Sleep for the duration mentioned in the config file
        #Also add a mechanism to check if the config file is updated, if updated then break so that it will read from config again
        pass

def write_to_prometheus():
    pass


if __name__ == "__main__":
    #TODO read the config file and assign to the variables
    #Check datastore type, if prometheus get it from get_data_from_promethues(metric_name, start_time, end_time, url)
    #Check if there's a trained model available for the given metric, else do the training also check the retrain flag in the config of each metric
    #Give predictions back to the prometheus if trained model is available locally
    with open('./config.yaml') as f:
        data = yaml.load(f, Loader=SafeLoader)
    #print(data)

    metric_dict = defaultdict(list)
    for elements in data['metrics']:
        for element in elements:
            metric_dict[element].append(elements[element])

    metric_name = metric_dict['name']
    start_time = metric_dict['start_time']
    end_time = metric_dict['end_time']
    url = data['prometheus_url']
    prom_query = metric_dict['query']
    forecast_every = metric_dict['forecast_every']

    data_for_training = get_data_from_prometheus(metric_name,prom_query, start_time, end_time, url)
    print(data_for_training)
    



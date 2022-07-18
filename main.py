#TODO import necessary packages

def get_data_from_prometheus(metric_name, start_time, end_time, url):
    data_points = []
    return data_points

def train_model():
    pass

async def predict_datapoints(metric['forecast_every'], metric['name']..):
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
    data_for_training = get_data_from_prometheus(metric_name, start_time, end_time, url)
    for metric in metrics:
        predict_datapoints(metric['forecast_every'], metric['name']..)
    while True:
        #get status of the async functions and restart failed ones
        time.sleep(30)
        pass

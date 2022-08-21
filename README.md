# xforecast

## Overview
xforecast is realtime predictive tool which could be used for short term data predictions. 
xforecast can be easily configured to learn multiple data streams for shorter time period(less than 24 hrs) and predict the data points in future.

## How it works?
xforecast is an application written in Python. It can be run in a container and connect to your timeseries database to read the data points and write back the predicted data points. Currently xforecast only supports prometheus database.

## How to run?
You can start the application in 2 ways, either from source code or with docker and docker-compose. Running xforecast is easier with docker to get you started.
First we need to edit the configuration. Below is a sample config which predict `mem_usage` of linux server.

```
prometheus_url: http://<prometheus_url:port>

metrics:
 - name: memory_usage  #metric name
   start_time: '2022-08-17T09:23:00.000Z' #start time for the training data
   end_time: '2022-08-17T09:33:00.000Z' #end time for the training data
   query: 100 - ((node_memory_MemAvailable_bytes{instance="node-exporter:9100"} * 100) / node_memory_MemTotal_bytes{instance="node-exporter:9100"}) #query as in prometheus
   training_interval: 1h #amount of data should be used for training
   forecast_duration: 10m #How data points should be predicted, here it will predict for 5 mins
   forecast_every: 120 #At what interval the app do the predictions 
   forecast_basedon: 600 #Forecast based on past how many data points
   write_back_metric: forecast_mem_usage #Where should it write back the metrics

```

Once you have created the above configuration file, you can start the forecaster by running

```
docker-compose up -d
```

As a next step you can create dashboards in grafana or your favourite visualisation tool. The predicted datapoints of the metrics can be found at the vaule of `write_back_metric` configuration.

If you have multiple metrics to forecast, then you can append the details of those metrics to the configuration.

## Feature Roadmap
- Support for influxdb
- Support for multiple forecasting ML models
- Support for auto-ml to automatically decide right model for each metric
- Web dashboard to create the metric predictions and monitor the prediction accuracy and it's health
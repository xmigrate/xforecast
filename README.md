<p align="center">
  <a href="https://xforecast.readthedocs.io/en/latest/"><img src="./images/xforecast.png" alt="xforecast" width=60%></a>
</p>
<p align="center">
    <em>Xforecast, a light weight realtime plug and play tool for predictive analytics</em>
</p>
<p align="center">
<a href="https://github.com/xmigrate/xforecast/actions/workflows/test.yml" target="_blank">
    <img src="https://github.com/xmigrate/xforecast/actions/workflows/test.yml/badge.svg" alt="Test">
</a>
<a href="https://codecov.io/gh/xmigrate/xforecast" target="_blank">
    <img src="https://codecov.io/gh/xmigrate/xforecast/branch/main/graph/badge.svg?token=R3M0MPSVRT" alt="Coverage">
</a>
<a href="https://github.com/xmigrate/xforecast/actions/workflows/main.yml" target="_blank">
    <img src="https://github.com/xmigrate/xforecast/actions/workflows/main.yml/badge.svg?branch=main" alt="Build">
</a>
</p>

---

## Overview
xforecast is realtime predictive tool which could be used for short term data predictions. 
xforecast can be easily configured to learn multiple data streams for shorter time period(less than 24 hrs) and predict the data points in future.

## How it works?
xforecast is an application written in Python. It can be run in a container and connect to your timeseries database to read the data points and write back the predicted data points. Currently xforecast supports prometheus and influxdb.

## How to run?
You can start the application in 2 ways, either from source code or with docker and docker-compose. Running xforecast is easier with docker to get you started.
First we need to edit the configuration. Below is a sample config which predict `mem_usage` of linux server.

```
metrics:
- name: memory_usage  #metric name in prometheus
  data_store : 
    name : prometheus  
    url: http://host.docker.internal:9000
  start_time: '2022-09-09T12:49:00.000Z'
  end_time: '2022-09-09T12:50:00.000Z'
  query: 100 - ((node_memory_MemAvailable_bytes{instance="node-exporter:9100"} * 100) / node_memory_MemTotal_bytes{instance="node-exporter:9100"})
  forecast_every: 60 #At what interval the app do the predictions 
  forecast_basedon: 60 #Forecast based on past how many data points
  write_back_metric: forecast_mem_usage #Where should it write back the metrics
  models : 
    model_name: prophet
    hyperparameters:
      changepoint_prior_scale : 0.05 #determines the flexibility of the trend changes
      seasonality_prior_scale : 10 #determines the flexibility of the seasonality changes
      holidays_prior_scale : 10 #determines the flexibiity to fit the holidays
      changepoint_range : 0.8 #proportion of the history where the trend changes are applied
      seasonality_mode : additive #whether the mode of seasonality is additive or multiplicative
- name: cpu_usage  #metric name ininfluxdb
  data_store : 
    name : influxdb   
    url: 192.168.1.9
    port: 8086
    user : admin
    pass : admin
    db_name : telegraf
    measurement : cpu
  start_time: '2022-09-14 11:19:00'
  end_time: '2022-09-14 11:20:00'
  query: SELECT mean("usage_idle") *-1 +100 FROM "autogen"."cpu" WHERE ("host" = 'ip-172-31-31-81') AND time >= '2022-09-14 11:19:00' AND time <= '2022-09-14 11:20:00' GROUP BY time(10s) 
  forecast_every: 60 #At what interval the app do the predictions 
  forecast_basedon: 60 #Forecast based on past how many data points
  write_back_metric: forecast_cpu_use #Where should it write back the metrics
  models : 
    model_name: prophet
    hyperparameters:
      changepoint_prior_scale : 0.05 #determines the flexibility of the trend changes
      seasonality_prior_scale : 10 #determines the flexibility of the seasonality changes
      holidays_prior_scale : 10 #determines the flexibiity to fit the holidays
      changepoint_range : 0.8 #proportion of the history where the trend changes are applied
      seasonality_mode : additive #whether the mode of seasonality is additive or multiplicative
```

Once you have created the above configuration file, you can start the forecaster by running

```
docker-compose up -d
```

As a next step you can create dashboards in grafana or your favourite visualisation tool. The predicted datapoints of the metrics can be found at the valuee of `write_back_metric` configuration.

If you have multiple metrics to forecast, then you can append the details of those metrics to the configuration.

## Feature Roadmap
- Support for multiple forecasting ML models
- Support for auto-ml to automatically decide right model for each metric
- Web dashboard to create the metric predictions and monitor the prediction accuracy and it's health

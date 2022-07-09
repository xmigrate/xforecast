# kube-forecast

## Overview
Kubeforecast helps to predict the data points for a given time period of a metric. It learns from the past data points of that metric.
We will be using pre-trained models for this purpose.

## Architecture

![Alt text](images/forecaster.PNG?raw=true "Architecture diagram of kube-forecast")

Kubeforecast has the following components,

- Datastore
- Visualizer
- Forecaster

### Datastore
We will be using prometheus as the supported datastore initially since the majority of the engineers uses this tool for collecting metrics from k8s cluster. Datastore will be used to query the datapoints of the metrics to be predicted by the forecaster. Datastore will be used by the forecaster to write the forecasted data points of that metrics.

### Visualizer
We use Grafana to plot the graph against the actual data points and forecasted data points of the metrics. This can be the same grafana that the engineers already have. Grafana can be used to set alerts to remediate the issue proactively with automated or manual means.

### Forecaster
Forecaster is an always-running application written Python. It reads the configurations such as the datastore url, metric name, training data hrs etc. from the config file. This config can be loaded as a configmap. Once the training is completed, it will start predicting the data points for x period in every y mins. Here x and y are loaded from the configuration. the predicted data points will be written back to the datastore.

#### ML Model
We need to consider models which can be trained with multi-dimensional data(multiple metrics)




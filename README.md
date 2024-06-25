# Software for non-residential electricity consumption forecasting.
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/system-architecture.png" width="800">

Software developed based on the prior [comparative model analysis](https://github.com/CyrilleSmid/load-prediction-research-notebook)

## Problem
Problem class: Time series regression </br>
[Input Data:](https://figshare.com/articles/dataset/CU-BEMS_Smart_Building_Electricity_Consumption_and_Indoor_Environmental_Sensor_Datasets/11726517/4) Time series of electricity consumption by sensor, categorised by building zones and power consumption type </br>
Output data: 
- total electricity consumption forecast
- model performance metrics
- real-time sensor power consumption visualization
- visualization of system monitoring metrics
  
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/input-data.png" width="800">

## Relevance
Applications of power management systems:
- peak load management
- time-of-use pricing
- demand management
- maintenance planning

## Goals and Objectives
#### Work Objective:</br>
Power consumption forecasting by developing a software solution for monitoring, visualization, and predictive analysis of an individual building electricity consumption.</br>

## Selected model architecture - LSTM
Input 1: Time series of the total power consumption with the lag of 7 days </br>
Input 2: Whether the next day is a work day or not (0/1)

<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/lstm-architecture.png" width="400">

```python
  input1 = Input(shape=(TIME_STEPS, INPUT_SHAPE))
  input2 = Input(shape=(1,))  
  
  lstm1 = LSTM(units=128, return_sequences=True)(input1)
  lstm1 = Dropout(0.2)(lstm1)
  
  lstm2 = LSTM(units=64, return_sequences=True)(lstm1)
  lstm2 = Dropout(0.2)(lstm2)
  
  lstm3 = LSTM(units=32, return_sequences=True)(lstm2)
  lstm3 = Dropout(0.2)(lstm3)
  
  lstm4 = LSTM(units=64, return_sequences=True)(lstm3)
  lstm4 = Dropout(0.2)(lstm4)
  
  lstm5 = LSTM(units=32, return_sequences=False)(lstm4)
  lstm5 = Dropout(0.2)(lstm5)
  
  fl_1 = Flatten()(lstm5)
  concatenated = concatenate([fl_1, input2])
  
  dense_1 = Dense(units=16)(concatenated)
  dense_2 = Dense(units=8)(dense_1)
  dense_3 = Dense(units=5)(dense_2)
  output = Dense(units=OUTPUT_SHAPE)(dense_3)
  
  model = Model(inputs=[input1, input2], outputs=output)
```

## User Interface
#### User authorization page
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/ui/ui-authorization.png" width="600">

#### Electricity consumption monitoring page
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/ui/ui-load-monitoring.png" width="600">

#### System monitoring page
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/ui/ui-sys-monitoring.png" width="600">

#### Electricity consumption forecast page
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/ui/ui-forecast.png" width="600">

## Technology stack
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/tech-stack.png" width="500">

## Model performance
<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/model-performance/results-table.png" width="400">

<img src="https://github.com/CyrilleSmid/sensor-load-pipeline/blob/main/readme_resources/model-performance/results-mape-change.png" width="500">



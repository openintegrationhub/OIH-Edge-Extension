[Go back](../../README.md)

# Anonymizer-Stream

## Description
With this component it is possible to anonymize the time series data of a subscribed topic and to write it into a target topic.
5 functions are implemented for the anonymizer:

1. hider: Preselected sensors are ignored.
2. skipN: Every N-th data point is forwarded.
3. thresholder: Values above/below a predefined threshold are replaced by a custom value or deleted. The custom value can also be the mean value of the current data set.
4. randomizer: A random value is added to each data point. The distribution can be customized by the user.
5. categorizer: The data is mapped according to user defined categories.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
config= {
   'source_topic':'stream_ann_source',
   'anonymized_topic':'stream_ann_sink',
   'faust_config':{
         id:,
         broker:)
   },
   'sensor_config': {
     'default': {
         'name':'thresholder',
             'window': 10,
             'threshold':[100,200],
             'substitution': [120,180]  also calcuation or deletion
             of th sub values is possible. e.g. ('delete','mean')
         },
     'Sensor2':{
         'name':'skip_n',
             'N': 10,
         },
     'Sensor3':{
         'name':'featex',
             'window': 10,
             'feature': ['mean','std','var','kurtosis']
         },
     'Sensor4':{
         'name':'randomizer',
             'window': 10,
             'percent': 0.5,
             'distribution': {'name': 'win_dist',
                              'std': 1
                               },
                             {'name': 'random',
                             'range': (1,100)
                               }
         },
     'Sensor5':{
         'name':'hider',
         },
     'Sensor6':{
         'name':'categorizer',
         'cats':[0,10,20,30,40,50],   categories <10, 10-20, 20-30, 30-40,
               >40   -float("inf")
         'labels':[1,2,3,4,5]    len(labels) must be len(cats)-1
         },
     }
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run anonymizer**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


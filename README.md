# OIH Edge

Open source framework for IIOT Edge Use Cases as part of the Open Integration Hub.

## Overview

The OIH Edge is a lightweight Python application for Edge connectivity and processing. It will help you to integrate your devices with third party systems through the OIH Platform. 

## Deployment


### Docker 

1. Clone the repository
2. Create your own Edge Flow configuration or use an existing demo configuration and copy it to the main_config folder
3. Build and run the Docker container with the following command:
   - **docker-compose build**
   - **docker-compose run app**

## Edge Flow Configuration

Edge Flow configurations consists of a buffer configuration and a step configuration. The first component of the step configuration is always a connector component (MQTT, OPCUA, DB Connector,...).  Any number of components can be connected downstream of the connector. Usually the last step is a database or webhook component to either persist the data or to transfer it to an OIH flow.

Example Edge Flow configuration:




        "name": "example flow",
        "description": "An example flow with 4 Steps.",
        "buffer": {
                "config": {
                    "type": "local",
                    "database": {},
                    "maxsize": 1000,
                    "maxpolicy": "override"
                                }
                },
        "steps": [
                    {
                    "name": "connector",
                    "config": {}
                    },
                    {
                    "name": "component1",
                    "config": {}
                    },
                    {
                    "name":"component2",
                    "config":{}
                    },
                    {
                    "name": "component3",
                    "config": {}
                    }
        ]


## Component Configurations

In OIH Edge we have 3 types of components: Source, analytic and sink components. The Source components are always the first step of the OIH Edge Flow. The task of these components is to establish connectivity (to an iot device) and to carry out user-defined data mapping.

### _Source components_

MQTT Connector

     "name": "connector",
     "config": {
                "host": "",
                "port": "",
                "clientid":"",
                "security": {
                              "cert_file": "",
                              "username": "",
                              "password": ""
                            },
       "topic": "",
       "mapping": [{
             "topicName": "",
             "converter": {
                    "type": "linemetrics"
                    }}
       ]
     }

OPCUA Connector

    {
        "name": "connector",
        "config": {
            "url": "",
            "username": "",
            "password": "",
            "deviceid": "",
            "nodeids": ["ns=3;i=1012", "ns=3;i=1018", "ns=3;i=1013"],
            "pol_time": 0.5}
    }

### _Analytic components_

Aggregator

The OIH Edge Aggregator component is compatible with the _pandas package_ and accepts every pandas aggregate function as method input.

    Example User configuration of the Aggregator component.
        'config':{ 
                'default': {"method":'mean',
                            "window_size":'5s'},	                            
                'sensor2': {"method":'last',
                            "window_size":'10s'} 
                            }
                    '...':{...}

Anonymizer

    Example User configuration of the Anonymizer component.
    'config'={ 
        'default': {
            'name':'thresholder',
                'window': 10,
                'threshold':(100,200),
                'substitution': (120,180)  #also calcuation or deletion of th sub values is possible. e.g. ('delete','mean')
            },
        'Sensor2':{
            'name':'skipN',
                'N': 10,
            },
        'Sensor4':{
            'name':'randomizer',
                'window': 10,
                #'percent': 0.5, 
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
            'cats':[-float("inf"),10,20,30,40,float("inf")],   #categories <10, 10-20, 20-30, 30-40, >40   #-float("inf") 
            'labels':[1,2,3,4,5]    #len(labels) must be len(cats)-1 
            oder
            'cats':(-30,130,50)
            'labels':False
            },
        }

### _Sink components_

Webhook Connector

    User configuration of Webhook component.
    {
                "name": "webhookconnector",
                "config": {
                    "url": "http://webhooks.localoih.com/hook/flowID"
                }
            }

MongoDB Connector

    {
        "name": "mongodbconnector",
        "config": {
            "ip": "",
            "port": "",
            "db": "test_db",
            "collection": "test_agg_data",
            "username": "",
            "password": ""
        }
    }

Influx Connector

    User configuration of the Influx component.
    {
    "name": "influxdbconnector",
    "config": {
            "host": "",
            "port": "",
            "db": "edge_adapter_test_db",
            "measurement": "linemetrics_mqtt_data",
            "username": "",
            "password": ""
            }}

## Data Format

## Test Setup


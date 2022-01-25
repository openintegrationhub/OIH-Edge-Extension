[Go back](../../README.md)

# OPCUA-Producer

## Description
This component subscribes to or polls data from one or more OPCUA nodes which can also be discovered for more data sources and writes this data into a Kafka topic.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
#   "name": "opcua_producer",
#   "kafka_broker": "localhost:9092",
# 	"sink_topic": "opcua",
# 	"opcua_url": "opc.tcp://192.168.0.1:4840",
# 	"security": {
# 		"password": "user",
# 		"username": "user"
# 	},
# 	"timeOut": 200,
# 	"deviceid":"Machine1",
#   "mode": {
#       "mode": "sub",
#       "discovery": "True",
#       "nodeids": ["ns=4;i=5001"],    # nodes to be subscribed to or to be discovered
#       "type": ["TagType"]            # Default: "BaseDataVariableType",
#       "toIgnore": ["Views", 
#                    "Types", 
#                    "Server"],        # folders and objects to be ignored while browsing through the address space
#       "subCheckTime"/"pol_time":     # 100/5 depending on mode that is used: "discPol" and "subCheckTime" in milli seconds and
#                                        seconds for "sub"/"discSub"/pol_time"
#   }
# }
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run opcua**
  


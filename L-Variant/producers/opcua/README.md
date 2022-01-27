[Go back](../../README.md)

# OPCUA-Producer

## Description
This component subscribes to or polls data from one or more OPCUA nodes which can also be discovered for more data sources and writes this data into a Kafka topic.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
   "name": "opcua_producer",
   "kafka_broker": "localhost:9092",
 	"sink_topic": "opcua",
 	"opcua_url": "opc.tcp://192.168.0.1:4840",
 	"security": {
 		"password": "user",
 		"username": "user"
	},
   "timeOut": 200,
   "deviceid":"Machine1",
   "mode": {
       "mode": "sub",
       "discovery": "True",
       "nodeids": ["ns=4;i=5001"],    
       "type": ["TagType"],            
       "toIgnore": ["Views", 
                    "Types", 
                    "Server"],        
      "subCheckTime"/"pol_time":
  }
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run opcua**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


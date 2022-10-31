[Go back](../../README.md)

# OPCUA-Producer

## Description

This component subscribes to or polls data from one or more OPCUA nodes which
can also be discovered for more data sources and writes this data into a Kafka
topic.

## Configuration

Configuration can be supplied by filling out required fields in config.json
file as seen below.

```
{
#   "name": "opcua_producer",
#   "kafka_broker": "localhost:9092",
#   "sink_topic": "kafka_source_component_test",
#   "opcua_host": "opc.tcp://192.168.0.1:4840",
#   "security": {
# 	"password": "user", # it is possible to leave that dict empty
# 	"username": "user"
#   },
#   "time_out": 200,
#   "mode": "subscription",
#   "node_ids": [],
#   "check_time": 2000,
#   "discovery": true,
#   "discovery_config": {
# 	"to_ignore": ["Views", "Types", "Server"], # Nodes to be ignored
# 	"node_type": ["BaseDataVariableType"] # Node type of subscribable nodes
#   }
# 
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
  

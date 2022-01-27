[Go back](../../README.md)

# MQTT-Producer

## Description
This component subscribes to one or more topics of an MQTT broker and writes this data into a Kafka topic.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
   "name": "mqtt_producer",
   "kafka_broker": "",
   "sink_topic": "mqtt",
   "mqtt_broker": "localhost",  
   "mqtt_port": 1883,
   "deviceid":"device_4711",
   "security": {
      "cert_file": "path",
      "username": "user",
      "password": "password"
  },
  "mqtt_topics": "Server1/sensor1",1),("Server2/sensor2"),1), ...],
  "mapping": [{
      "topicName": "account/1994",
      "converter": {
          "type": "linemetrics",
          "filter": {
          }
  }]
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run mqtt**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


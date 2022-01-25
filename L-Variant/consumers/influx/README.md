[Go back](../../README.md)

# Influx-Consumer

## Description
This component consumes data from a topic and writes it into an InfluxDB measurement.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
   "name": "influx_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "opcua_kafka",
   "influx_host": "localhost",
   "influx_port": "8086",
   "influx_db": "demo",
   "influx_measurement": "opcua",
   "influx_username": "admin",
   "influx_password": "admin"
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run influx**
  


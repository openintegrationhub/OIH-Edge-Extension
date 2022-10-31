[Go back](../../README.md)

# Modbus-Producer

## Description

This component reads data from one or multiple Modbus registers and writes
the data into a kafka topic.

## Configuration

Configuration can be supplied by filling out required fields in config.json
file as seen below.

```
{
#   "name": "modbus_producer",
#   "kafka_broker": "localhost:9092",
#   "slaves": [{
#     "host": "localhost",
#     "port": 5022,
#     "topic": "Temp",
#     "method": "read_input",
#     "start_adress": 0,
#     "count": 1,
#     "unit": 1
#   },
#   {
#     "host": "localhost",
#     "port": 5022,
#     "topic": "Pressure",
#     "method": "read_holding",
#     "start_adress": 0,
#     "count": 1,
#     "unit": 1
#   }],
#   "timeout_attempts": 30
}
```

## Deployment

Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
    - **docker-compose build**
    - **docker-compose run modbus**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  

[Go back](../../README.md#components)

# IIoT-Simulator

## Description

This component generates IIoT simulation data and writes this data in a Kafka
topic. It can be used for demo cases with the Payperuse component. You can
either generate evenly spaced data or read data from a csv file.

## Configuration

Configuration can be supplied by filling out required fields in config.json
file as seen below.

Configuration example to use the custom iiot-simulator.

```
{
	"bootstrap_servers": "localhost:19092",
	"topic": "kafka_source_component_test",
	"key": "kafka_source",
	"simulator_config": {
		"type": "custom",
		"period": 10,
		"interval": 1,
		"sensors": {
			"sensor01": [50,999],
			"sensor02": [10,240],
			"sensor03": [30,555],
			"sensor04": [10,120]
		}
	}
}

```

Configuration example to use the csv iiot-simulator.

```
{
	"bootstrap_servers": "localhost:19092",
	"topic": "kafka_sink_component_test",
	"key": "kafka_source_csv",
	"simulator_config":{
        	"type":"csv",
        	"interval" : 10,
        	"timestamp": "auto",
        	"csv_config":{
				"sep":";",
				"header":0,
				"usecols":["Sensor1","Sensor2","Sensor3","Sensor4"]}
			}
		}
```

## Deployment

Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
    - **docker-compose build**
    - **docker-compose run iiotsimulator**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


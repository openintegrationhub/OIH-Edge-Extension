[Go back](../../README.md)

# IIoT-Simulator

## Description
This component generates IIoT simulation data and writes this data in a Kafka topic. It can be used for demo cases with 
the Payperx component.

## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
config:{
	"bootstrap_servers":"",
	"topic" : "iiot-simdata",
	"key": "iiot-sim",
	"period" : 60,
	"interval": 1,
		"sensors":{
			"zk_spannung": [50,999],
			"zk_strom": [10,240],
			"wr_spannung": [30,555],
			"wr_strom": [10,120]
		}
		}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run iiot-simulator**
  


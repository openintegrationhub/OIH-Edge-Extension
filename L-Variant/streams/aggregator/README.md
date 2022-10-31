[Go back](../../README.md)

# Aggregator-Stream

## Description
With this component it is possible to aggregate the time series data of a subscribed topic over a certain window size and to write it into a target topic.
The Aggregator component is compatible with the pandas package and accepts every pandas aggregate function as method input.

## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
config = {
	"source_topic": "kafka_stream_component_agg_source",
	"aggregated_topic": "kafka_source_component_agg_sink",
	"faust_config": {
		"id": "agg_test",
		"broker": "kafka://localhost:19092",
		"port": 6067
	},
	"sensor_config": {
		"default": {
			"method": "mean",
			"window_size": "5s"
		},
		"sensor01": {
			"method": "median",
			"window_size": "5s"
		}
	}
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run aggregator**
  
To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  

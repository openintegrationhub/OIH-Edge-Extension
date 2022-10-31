[Go back](../README.md)

# Component-Name

## Description
Describe the components function and usage.


## Configuration
Describe how configuration of the component works and supply an example like seen below 

```
{
	"payperuse_config": {
        "source_topic": "kafka_stream_component_ppu_source",
        "aggregated_topic": "kafka_source_component_ppu_sink",
        "window_size": 10,
        "node_sets": [["sensor01", "sensor02"], 
                     ["sensor03", "sensor04"]],
        "price_per_consumption": 0.145,
        "price_per_unit": 0.1,
        "fix_costs": 0.0031623,
        "risk_costs": 200,
        "minimum_acceptance": 5760

    },
   "faust_config":{
         "id": "payperuse5",
         "broker": "kafka://localhost:9092",
         "port": 6068
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run payperuse**
  


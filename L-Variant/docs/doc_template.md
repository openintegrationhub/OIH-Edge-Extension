[Go back](../README.md)

# Component-Name

## Description
Describe the components function and usage.


## Configuration
Describe how configuration of the component works and supply an example like seen below 

```
{
	"payperx_config":{
        "source_topic": "opcua",
        "aggregated_topic": "payperx_test",
        "interval": 10,
        "bufferType": {
            "mode": "inMemory"
        },
        "nodesets": [["ns=4;s=ZK_Spannung", "ns=4;s=ZK_Strom"], ["ns=4;s=WR_Spannung", "ns=4;s=WR_Strom"]],
        "kWh": 0.145,
        "stk": 0.1,
        "fix": 0.0031623,
        "risk": 200,
        "minStk": 5760

    },
    "faustapp_config":{
			"id": "",
            "broker": ""
        }
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run payperx**
  


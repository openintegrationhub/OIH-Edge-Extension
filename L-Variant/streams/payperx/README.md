[Go back](../../README.md#components)

# Pay-Per-X Component as Faust Stream

## Description

The Pay-Per-X component can be used to demonstrate a pay-per-use model that produces certain performance indices like 
risk or total cost. These values are calculated with the machine data that is produced by the IIoT-Simulator component.

The Formulas for said indices are defined as:

> -index of use: current * voltage * duration * price/consumption = consumptionCosts
> 
> current and voltage are specified as sensor data and the price/consumption is specified in the config.

> -risk index: riskCost * (quantity/minimimQuantity) = riskCosts
>
> riskCost and minimumQuantity is specified in the config.

> -fix: fixedCost/time * duration = fixedCosts
> 
> fixedCost/time is specified in the config.

> -total: accumulatedConsumptionCost + accumulatedRiskCost + accumulatedFixCost = totalCost

## Configuration
The configuration consist of the payperx component configuration (payper_xonfig) and the faust app configuration (faustapp_config). 

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
   "faust_config":{
         "web_port"='',
         "id": '',
         "broker": '')
}
```

## Deployment
When you want to deploy your Stream, you should...

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run payperx**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


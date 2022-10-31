[Go back](../../README.md#components)

# Payperuse Component as Faust Stream

## Description

The Pay-Per-Use component can be used to demonstrate a pay-per-use model that
produces certain performance indices like
risk or total cost. These values are calculated with the machine data that is
produced by the IIoT-Simulator component.

The Formulas for said indices are defined as such:

> -index of use: current * voltage * duration * price/consumption =
> consumptionCosts
>
> current and voltage are specified as sensor data and the price/consumption is
> specified in the config.

> -risk index: riskCost * (quantity/minimimQuantity) = riskCosts
>
> riskCost and minimumQuantity is specified in the config.

> -fix: fixedCost/time * duration = fixedCosts
>
> fixedCost/time is specified in the config.

> -total: accumulatedConsumptionCost + accumulatedRiskCost + accumulatedFixCost
> = totalCost

## Configuration

The configuration consist of the payperuse component configuration 
(payperuse_onfig) and the faust app configuration (faustapp_config).

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

When you want to deploy your Stream, you should...

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
    - **docker-compose build**
    - **docker-compose up**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


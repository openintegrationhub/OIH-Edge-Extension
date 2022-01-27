[Go back](../../README.md)

# Webhook-Consumer

## Description
This component consumes data from a topic and sends it to a defined webhook endpoint via http request.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
   "name": "webhook_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "opcua",
   "webhook_url": "https://webhook.site/test"
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run webhook**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


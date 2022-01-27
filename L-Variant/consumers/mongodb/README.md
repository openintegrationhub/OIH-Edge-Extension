[Go back](../../README.md)

# MongoDB-Consumer

## Description
This component consumes data from a topic and writes it into a MongoDB collection.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
	"name": "mongodb_consumer",
   	"kafka_broker": "localhost:9092",
   	"source_topic": "mqtt",
   	"mongodb_host": "localhost",
   	"mongodb_port": "27017",
	"mongodb_username": "root",
	"mongodb_password": "rootpassword",
	"mongo_db": "mqtt",
	"mongodb_collection": "linemetrics"
}
```

## Deployment
Describe how the component can be deployed like seen below

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run mongodb**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


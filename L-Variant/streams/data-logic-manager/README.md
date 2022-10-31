[Go back](../../README.md)

# Data-Logic-Manager

With this component a rules engine environment is setup composed of:

* Drools Workbench
* Kie Server
* "DLM" Faust stream(s)

## Drools Workbench
Contains the database and web frontend for project management (i.e: "Rule creation/managing")

[Workbench docs](https://docs.jboss.org/drools/release/6.2.0.CR3/drools-docs/html/wb.Workbench.html)

## Kie Server
"Execution server" providing an interface exposing the API to "rule check" data.

[Kie Server docs](https://docs.drools.org/6.5.0.CR2/drools-docs/html/ch22.html)

## DLM Stream(s)
Our own custom component capable of rule checking multiple data types simultaneously. Parallel streams are run each with it´s own configuration which allows for parameters such as:
* Project's container ID
* Input and output topics 
* Data structure.

In this component, the datatype is not hardcoded but rather composed "programatically" based on the parameters provided on the config, with the intention that the stream codebase will not be needed to change (Ideally) regardless of the use case. At the moment only "flat" data structures are possible this way, but this can be expanded to multidimensional data too.


## Configuration
Configuration can be supplied by filling out required fields in config.json file as seen below. 

```
{
    "application_name":"drools-stream",
    "broker":"kafka://yourbroker:port",
    "kie_server": {
        "host": "http://kie:8080",
        "username": "kiepass",
        "password": "kiepass!",
        "containers": [
            {
                "container_package": "com.myspace.vibrations",
                "container_id": "Vibrations_1.0.0-SNAPSHOT",
                "input_topic":"test-dlm-vibration-parts-raw-1",
                "output_topic":"test-dlm-vibration-parts-sink",
                "object": {
                    "name": "Part",
                    "fields": ["id", "machine_id", "vibration_level_1", "vibration_level_2", "vibration_level_3", "quality_class", "timestamp"]
                }
            },
            {
                "container_package": "com.myspace.vibrations",
                "container_id": "Vibrations_1.0.0-SNAPSHOT",
                "input_topic":"test-dlm-vibration-parts-raw-2",
                "output_topic":"test-dlm-vibration-parts-sink",
                "object": {
                    "name": "Part",
                    "fields": ["id", "machine_id", "vibration_level_1", "vibration_level_2", "vibration_level_3", "quality_class", "timestamp"]
                }
            },
            {
                "container_package": "com.myspace.product",
                "container_id": "Products_1.0.0-SNAPSHOT",
                "input_topic":"test-dlm-products-parts-raw-1",
                "output_topic":"test-dlm-products-parts-sink",
                "object": {
                    "name": "Product",
                    "fields": ["id", "price", "category", "status", "timestamp"]
                }
            }
        ]
        
    }
}
```

## Deployment
Steps:

1. clone the repository
2. create a configuration file (config.json) and copy it to the config folder
3. build and run the Docker container with the following commands:
   - **docker-compose build**
   - **docker-compose run dlm**
  
To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  


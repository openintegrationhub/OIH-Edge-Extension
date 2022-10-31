[Go back](../../README.md)

# Influx-Consumer

## Description

This component consumes data from a topic and writes it into an InfluxDB
measurement. It is possible to write data with different schemas into the
InfluxDB, due to the addition of a generic mapper.

## Configuration

Configuration can be supplied by filling out required fields in config.json
file as seen below. If the schema field is left empty, the influx expects
the standard data schema, if not it will map the data as specified in the
path fields.

```
For standard configuration:
{
   "name": "influx_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "kafka_sink_component_test",
   "influx_host": "localhost",
   "influx_port": "8086",
   "influx_db": "influx_consumer_database",
   "influx_measurement": "influx_consumer_measurement",
   "influx_username": "admin",
   "influx_password": "admin",
   "schema": []
}
Configuration with mapper:
{
   "name": "influx_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "kafka_sink_component_test",
   "influx_host": "localhost",
   "influx_port": "8086",
   "influx_db": "influx_consumer_database",
   "influx_measurement": "influx_consumer_measurement",
   "influx_username": "admin",
   "influx_password": "admin",
   "schema": [{
      "name_pos": ["data_body", "field"],
      "name": "sensor01",
      "value_pos": ["data_body", "value", "val"],
      "timestamp_pos": ["data_body", "timestamp"],
      "metadata_pos": ["metadata"],
      "field_name": "sensor01" # This field is used to change the name 
                                    if necessary
   }]
}
Expects data in the following schema:
   {
      "data_body": {
         "field": "sensor01",
         "timestamp": "2022-06-07T11:16:00:00000",
         "value": {
            "val": 50 ([50, 100, 200] lists are also possible to be expected)
         }
      }
   }
Configuration without name_pos:
{
   "name": "influx_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "kafka_sink_component_test",
   "influx_host": "localhost",
   "influx_port": "8086",
   "influx_db": "influx_consumer_database",
   "influx_measurement": "influx_consumer_measurement",
   "influx_username": "admin",
   "influx_password": "admin",
   "metadata_path": ["metadata"], # In this example it is possible and
                                    recommended to use metadata_path
                                    instead of metadata_pos
   "schema": [{
      "value_pos": ["data", "sensor01", "value"],
      "timestamp_pos": ["data", "sensor01", "timestamp"],
      "field_name": sensor01
   }]
}
Expects data in the following schema:
   {
      "data": {
         "sensor01": [{
            "value": 500, "timestamp": "2022-06-07T11:16:00:00000"
         }]
      },
      "metadata": {}
   }
Configuration with data_path:
{
   "name": "influx_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "kafka_sink_component_test",
   "influx_host": "localhost",
   "influx_port": "8086",
   "influx_db": "influx_consumer_database",
   "influx_measurement": "influx_consumer_measurement",
   "influx_username": "admin",
   "influx_password": "admin",
   "metadata_path": ["metadata"],
   "schema": [{
      "data_path": ["data"],
	  "name_pos": ["body", "field"],
	  "name": "sensor01",
	  "value_pos": ["body", "value", "val"],
	  "timestamp_pos": ["body", "timestamp"],
	  "field_name": "sensor01" 
   }]
}
Expected schema:
   {
      "data": [{
         "body": {
            "field": "sensor01",
            "value": {
               "val": 50
            }
            "timestamp": "2022-06-07T11:16:00:00000"
         }
      },
      {
         "body": {
            "field": "sensor02",
            "value": {
               "val": 50
            }
            "timestamp": "2022-06-07T11:16:00:00000"
         }
      }],
      "metadata": {}
   }
In this example only the data with the name sensor01 will be
used.
Config with a list in value_pos:
Configuration with mapper:
{
   "name": "influx_consumer",
   "kafka_broker": "localhost:9092",
   "source_topic": "kafka_sink_component_test",
   "influx_host": "localhost",
   "influx_port": "8086",
   "influx_db": "influx_consumer_database",
   "influx_measurement": "influx_consumer_measurement",
   "influx_username": "admin",
   "influx_password": "admin",
   "schema": [{
      "name_pos": ["data_body", "field"],
      "name": "sensor01",
      "value_pos": ["data_body", "value", ["val1", "val2", "val3"]],
      "timestamp_pos": ["data_body", "timestamp"],
      "metadata_pos": ["metadata"],
      "field_name": "sensor01" # This field is used to change the name 
                                    if necessary
   }]
}
Expected schema:
   {
      "data_body": {
         "field": "sensor01",
         "timestamp": "2022-06-07T11:16:00:00000",
         "value": {
            "val1": 50,
            "val2": 100,
            "val3": 200
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
    - **docker-compose run influx**

To stop the containers use:
> - **docker-compose stop**
>
> or
> - **docker-compose down** (deletes the containers after stopping)
  

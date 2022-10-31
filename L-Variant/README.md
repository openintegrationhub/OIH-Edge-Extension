<center><h1>OIH Edge Extension L-Variant</h1></center>

## Introduction

The **OIH Edge Extension L-Variant** is a software solution for deploying,
connecting and managing different IIoT data
producers, consumers and processing streams. It is based on Apache Kafka and
uses a mesh of Edge Flow components that
write their data into Kafka topics and can dynamically be connected to each
other in order to realize complex data
pipelines and multi-connectivity.

## Content

- [Overview](#overview)
- [Deployment](#deployment)
- [Components](#components)
- [Data format](#data-format)
- [Contribution](#contribution)

<hr>

## Overview

The diagram seen below shows the architecture of the OIH Edge Extension
L-Variant and gives an overview of the
available components.

![Overview of OIH Edge architecture](./docs/assets/l_variant_overview.png)

### Kafka broker

The Kafka broker is the main component that all producers, consumers and
streams connect to in order to write their data
into a topic or subscribe to topics to consume data. If a component wants to
write data into a topic that doesn't exist
it is created automatically.

### Kafka Zookeeper

The Kafka broker connects to the Zookeeper which holds records of the broker's
metadata and is essential for
coordinating more than one broker within a Kafka cluster.

### Kafka UI

Kafka-UI is an open source Kafka management tool and can be accessed by a web
browser via the address:
> http://localhost:8080

Kafka-UI provides a web interface for inspecting the current state of the
connected Kafka cluster or managing topics and
messages.

## Deployment

### Requirements

The requirements to run the API are the following:

> 1. Node.js
> 2. Npm
> 3. Python
> 4. Docker

If you want to run the software without the API, you only need docker.

### Initial Deployment

For the deployment you need to go to the directory ./api/dist and run
startup.exe, it will check if node.js, npm and python are installed. If so, it
will automatically install all dependencies and then run the API. When the API
is started, a Kafka Cluster will also be deployed. At that point you can start
new containers and manage them via the Endpoints. You can look up the Endpoints
via the SwaggerHub Editor, you just need to import the 'Endpoints.json'-File,
which is located in the docs folder.

If you want to run the software without the API, you only need to navigate
to the main directory of the project and use the following commands:

> 1. docker-compose build
> 2. docker-compose up

Afterwards you can start each component separately from their respective
directory.

The Kafka-UI can be accessed by a web browser via the following adress

> Kafka-UI: http://localhost:8080

## Components

All L-Variant components are deployed as single Docker containers and can be
divided in three different groups that are
similar to the S-Variant. Source components are realized as Kafka producers
that write machine data into a predefined
topic. Sink components are Kafka consumers that subscribe to topics in order to
process new messages and write the data
into a database or send it to a webhook. Analytics components however subscribe
to topics, process new messages and
write the result into another topic. <br>
A component base class can be inherited by all L-Variant components to
implement basic functionalities like a file and
Kafka logger, configuration via environment variables or config file and a
system signal listener for gracefully shutting
down the component on external docker shutdown events.
The following sub-chapters describe how to configure and deploy these
components.

### [Component base class](./component_base_class/README.md)

### Source components (Producers)

- #### [IIoT-Simulator](./producers/iiot-simulator/README.md)
- #### [MQTT](./producers/mqtt/README.md)
- #### [OPCUA](./producers/opcua/README.md)
- #### [Modbus](./producers/modbus/README.md)

### Sink components (Consumers)

- #### [Influx](./consumers/influx/README.md)
- #### [Webhook](./consumers/webhook/README.md)
- #### [MongoDB](./consumers/mongodb/README.md)

### Analytics components (Streams)

- #### [Pay-per-use](./streams/payperuse/README.md)
- #### [Aggregator](./streams/aggregator/README.md)
- #### [Anonymizer](./streams/anonymizer/README.md)
- #### [Data-Logic-Manager](./streams/data-logic-manager/README.md)

## Data format

The OIH Edge Extension internal data scheme follows the OIH JSON data pattern
in which there is a `metadata` and `data`
tag. The `metadata` tag contains info like a machine ID or other identifiers
for the data source. The `data` tag
contains sensor IDs which are represented by tags that can store several data
value sets in an array as shown below. As
Kafka messages have a `key:value` structure all producers use a
predefined `machineID` that is used as `key` and the
original message as `value` when they write data into a topic.

```
{
    'metadata': {
        'deviceID': "MainOffice"
    },
    'data': {
        "Sensor1": [
            {"timestamp":"2021-07-30T09:24:29","value":"26.48"},
            {"timestamp":"2021-07-30T09:25:29","value":"27.48"}
        ]
    }
}
```

## Contribution

If you want to write a documentation for your component use
this [template](./docs/doc_template.md) as basic structure.

# <center>OIH Edge Extension</center>

# Introduction

OIH Edge Extension is an open source framework for IIoT edge device connectivity and data processing as part of the Open 
Integration Hub project. Its main purpose is helping users to integrate their devices in third party systems via the 
OIH platform. The OIH Edge Extension is available in two variants which are called S- and L-Variant.<br>

> The **S-Variant** is a lightweight Python application and can execute a single Edge Flow to realize a predefined data 
> pipeline. It can be deployed as a single Docker container or, depending on the test case, as a package that contains
> additional components such as InfluxDB, Chronograf and Grafana.
> 
> The **L-Variant** is based on Apache Kafka and uses a mesh of Edge Flow components that write their data into Kafka 
> topics and can dynamically be connected to each other in order to realize complex data pipelines and 
> multi-connectivity.    

# Content

[<h3>OIH Edge Extension S-Variant</h3>](./S-Variant/README.md)
- [Overview](./S-Variant/README.md#overview)
- [Deployment](./S-Variant/README.md#deployment)
- [Edge Flow configuration](./S-Variant/README.md#edge-flow-configuration)
- [Component configuration](./S-Variant/README.md#component-configuration)
- [Data format](./S-Variant/README.md#data-format)
- [Test setup](./S-Variant/README.md#test-setup)

[<h3>OIH Edge Extension L-Variant</h3>](./L-Variant/README.md)
- [Overview](./L-Variant/README.md#overview)
- [Components](./L-Variant/README.md#components)
- [Deployment](./L-Variant/README.md#deployment)
- [Data format](./L-Variant/README.md#data-format)
- [Contribution](./L-Variant/README.md#contribution)


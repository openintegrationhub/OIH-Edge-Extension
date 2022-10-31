[Go back](../README.md)

# Component base class

## Description

The component base class can be inherited by all L-Variant components to
implement basic functionalities like a file and Kafka logger, configuration
via environment variables or config file, a system signal listener for
gracefully shutting down the component on external docker container events
and the possibility to change configs while the component is still running,
for that matter there is also an agent manager which enables to change source
and sink topic for the stream components.

## Usage

In order to use the functionalities provided by the component base class it has
to be inherited from the L-Variant component and copied to its root directory.

Example:

```
import ComponentBaseClass

class LVariantComponent(ComponentBaseClass):
...
```

## Attributes

Docker containers can be stopped externally and, in most cases, force the
application to stop. The `self.terminated` variable can be used inside loops
in order to gracefully shut down the component. Its default value is `False`
and turns to `True` when an external system signal is received.

Example:

```
while not self.terminated:
   # do something
   ...
# clean up resources before shutdown
```

The config updates function via configuration files, therefore the path of
the file has to be specified. If not specified in the environmental
variables it will take the default path for the configuration, which is
just inside the configs folder.

## Methods

The two most important base class methods are `get_logger()` and `get_config()`
. They provide an easy implementation of different logging and configuration
functionalities.

### `get_logger()`

```
def get_logger(self, logger_type="file", file_path="/logs", max_log_files=0, kafka_config=dict) -> logging.Logger:
  Returns the standard logger with file- or Kafka-handler. Can also be called more than one time to combine
  both logging methods.

  :param logger_type: (str, optional) "file" for file logger, "kafka" for kafka logger. Defaults to "file".
  :param file_path: (str, optional) relative file path to log files. If directory doesn't exist it will be created.
      Defaults to "/logs".
  :param max_log_files: (int, optional) maximum number between 1 and 9 of backup log files used by logger.
      Defaults to 1.
  :param kafka_config: (dict, mandatory when "logger_type" is set to "kafka") Kafka configuration in form of dict like 
      {
       "bootstrap_servers": "localhost:9092", 
       "topic": "Kafka-Logging", 
       "key": "Component X" 
       [, "debug": True/False (optional)]
      }
      If value of "key" is left empty ("key": ""), a random key like "Kafka-Logger#aj3hxd8s" is created automatically. 
      If a "debug" key is present and set to True, all internal Kafka messages will be logged too.
      Use with caution! Kafka produces hundreds to thousands of messages per minute.
  :return: Logger
```

Example:

```
# basic call
self.logger = self.get_logger()
# parameter call
self.logger = self.get_logger(file_path="/test/logs", max_log_files=5)
# Kafka logger
kafka_config = {"bootstrap_servers": "localhost:9092", "topic": "Kafka-Logger", "key": "Test-Component"}
self.logger = self.get_logger(logger_type="kafka", kafka_config)
```

### `get_config()`

``` 
   def get_config(self, config: dict, source="env", file_path="/config", ) -> dict:
        Returns configuration from environment variables or configuration file.

        :param config: (dict) dict with required configuration keys. Keys found in environment variables are filled up
            with their respective values, missing keys get NULL value. Dict can be completely empty when using
            "file"-method.
        :param source: (str, optional) reads configuration from environment variables when set to "env" or from config
            file when set to "file". Defaults to "env".
        :param file_path: (str, optional) folder in which to search for config.json file. Defaults to "/config".
        :return: (dict) dictionary with configuration found in environment variables or configuration file.
```

Example:

```
config_template = {}
self.config = self.get_config(config_template, source="file")
print(str(self.config))
>> {"host": "localhost", "port": 8080}
```

```
config_template = {"user": "", "pass": ""}
self.config = self.get_config(config_template, source="env")
print(str(self.config))
>> {"user": "admin", "pass": "root"}
```

When you start a container with the API, the container will be started without
a config, it needs to be provided afterwards. Therefore the container will wait
for the config to be provided, this is achieved with the
`wait_for_config_insertion()` method, which will check for a config every 5
seconds and load the config after insertion.

### `wait_for_config_insertion()`

```
def wait_for_config_insertion(self) -> dict:
    Provides the component with the initial config given
    by the given config file. It either retrieves the last
    already existing config or if no config is given, it
    waits for the first config to be inserted.

:return: (dict) config
```

Example

```
def load_config(self, config_template, source='file'):
    if source = 'file':
        config = self.wait_for_config_insertion()
    else:
        config = self.get_config(config_template)
    ...
```

For the analytic components to work, it is required to define an app and attach
an agent to it. For that matter the component base class provides the
`create_app()` and the `create_agent()` methods:

### `create_app()`

```
def create_app(self,
               app_config):
    Create and configure a Faust app, with the given config.

    :param app_config: configuration of the faust app
```

### `create_agent()`

```
def create_agent(self,
                 source_topic: str,
                 sink_topic: str,
                 app: faust.App,
                 func: Callable):
    Create an agent and attach it to the given faust app.
    
    :param source_topic: (str) Name of the source topic.
    :param sink_topic: (str) Name of the sink topic.
    :param app: (faust App) given faust app.
    :param func: (Callable) process method of the respective component.
    :return: None
```

Example:

```
def load_config(self, config_template, source='file'):
    if source = 'file':
        config = self.wait_for_config_insertion()
    else:
        config = self.get_config(config_template)
    self.source_topic = config['source_topic']
    self.sink_topic = config['sink_topic']
    self.app_config = config['faust_app_config']
    self.app = self.create_app(self.app_config)
    self.create_agent(self.source_topic,
                      self.sink_topic,
                      self.app, 
                      self.process) # this method should be defined somewhere
                                    # in your analytics component
```
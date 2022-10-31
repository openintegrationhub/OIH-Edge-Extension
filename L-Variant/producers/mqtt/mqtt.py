# -*- coding: utf-8 -*-
"""
Created on Tue Jan  5 13:00:20 2022

@author: TRM
"""
# EXAMPLE CONFIG
# {
#   "name": "mqtt_producer",
#   "kafka_broker": "",
# 	"sink_topic": "mqtt",
# 	"mqtt_broker": "localhost",  #MQTT Broker hostname
#   "mqtt_port": 1883,
#   "deviceid":"device_4711",
#   "security": {
#       "cert_file": "path",
#       "username": "user",
#       "password": "password"
#   },
#   "mqtt_topics": "Server1/sensor1",1),("Server2/sensor2"),1), ...],
#   #List of tuples containing topic names as well as
#        QOS levels
#   "mapping": [{
#       "topicName": "account/1994",
#       "converter": {
#           "type": "linemetrics",
#           "filter": {
#           }
#   }]
# }
import json
from typing import Any

import paho.mqtt.client as mqtt
from component_base_class.component_base_class import ComponentBaseClass
from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError
from simplejson import JSONDecodeError
from simplejson import loads

from converter.mqttConverter import Converter as Converter


class MQTTProducer(ComponentBaseClass):
    def __init__(self):
        """
            Pull all data from the config file and initialize all major data
            variables to ensure that the program runs without problems
        """
        try:
            super().__init__()
        except Exception as error:
            print(f'Failure in Base Class, {error}')
            return
        # LOGGER
        self.logger = self.get_logger()

        config_template = {
            "name": "",
            "kafka_broker": "",
            "sink_topic": "",
            "mqtt_broker": "",
            "mqtt_port": 0,
            "deviceid": "",
            "security": "",
            "mqtt_topics": "",
            "mapping": ""
        }
        # CONFIG

        self.config = {}
        self.topic = ''
        self.producer = None
        self.statistics = {}
        self.device_id = ''
        self._client = None
        self.mqtt_broker = ''
        self.mqtt_port = ''
        self.mqtt_topics = ''
        self.converter = None
        self.load_config(config_template)
        self.connected = False
        self._client.on_message = self.on_message
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        if not self.terminated:
            self.start()

    def load_config(self, config_template: dict = None, source: str = 'file'):
        """Loads the config for the component, either from env variables
        or from a file.

        :param config_template: dict with all required fields for the
        component to work.
        :param source: source of the config, either file or env
        :return: None
        """
        if source != 'file':
            config = self.get_config(
                config_template,
                source=source,
                file_path=f'/config/{self.path_name}'
            )
        else:
            config = self.wait_for_config_insertion()
        self.config = config
        try:
            if config and all(key in self.config
                              for key in config_template.keys()):
                if "kafka_broker" in config and "sink_topic" in config:
                    self.topic = config["sink_topic"]
                    self.producer = KafkaProducer(
                        bootstrap_servers=[config["kafka_broker"]])
                self.statistics = {'MessagesReceived': 0, 'MessagesSent': 0}
                if self.device_id != self.config["deviceid"]:
                    self.device_id = self.config["deviceid"]
                    self._client = mqtt.Client(self.device_id)
                if "username" in self.config["security"]:
                    self._client.username_pw_set(
                        self.config["security"]["username"],
                        self.config["security"]["password"])
                if "cert_file" in self.config["security"]:
                    self._client.tls_set(self.config["security"]["cert_file"])
                self.mqtt_broker = self.config["mqtt_broker"]
                self.mqtt_port = self.config["mqtt_port"]
                self.converter = Converter(self.config["mapping"])
                self.mqtt_topics = self.config["mqtt_topics"]
            else:
                self.logger.error('Missing key(s) in config')
                print('Missing key(s) in config', flush=True)
                self.terminated = True
                return
        except Exception as error:
            self.logger.error(f'Error: {error} in load_config')
            self.terminated = True

    def __connect(self):
        """ Connect to a mqtt broker.

        :raise RuntimeError if connection fails.

        :return: None
        """
        try:
            self._client.connect(self.mqtt_broker, self.mqtt_port)
        except ValueError as val_err:
            self.logger.error('Invalid Credentials')
            raise RuntimeError('Mqtt Client unavailable!') from val_err

    def on_connect(self,
                   client: mqtt.Client,
                   userdata: Any,
                   flags: dict,
                   rc: int):
        """ Executed when connection to Mqtt broker was successful.
        Writes connection notification into logs and subscribes to
        specified topics.

        :param client: Client instance for this callback
        :param userdata: the private user data as set in Client() or
        user_data_set()
        :param flags: response flag sent by the broker
        :param rc: the connection result
        :return: None
        """
        self.connected = True
        self.logger.info("Connected to MQTT broker")
        self._client.subscribe(self.mqtt_topics)
        self.logger.info("Subscribed to topic " + self.mqtt_topics)

    def __disconnect(self):
        """ Disconnects from the Mqtt Broker and stops the loop.

        :return: None
        """
        self._client.loop_stop(force=False)
        self.logger.info("Loop status: stopped")
        self._client.disconnect()

    def on_disconnect(self,
                      client: mqtt.Client,
                      userdata: Any,
                      rc: int):
        """ Executes on disconnect. Writes notification into logs.

        :param client: Client instance for this callback
        :param userdata: the private user data as set in Client() or
        user_data_set()
        :param rc: the connection result
        :return: None
        """
        self.connected = False
        self.logger.info("Disconnected from MQTT Broker")

    def on_message(self,
                   client: mqtt.Client,
                   userdata: Any,
                   msg: mqtt.MQTTMessage):
        """ Executes when the broker sends a message.

        :param client: Client instance for this callback
        :param userdata: the private user data as set in Client() or
        user_data_set()
        :param msg: Messages sent by the broker
        :return: None
        """
        try:
            self.statistics['MessagesReceived'] += 1
            self.logger.info(
                "MQTT income=" + str(self.statistics['MessagesReceived']))
            content = self._decode(msg)
            result = self.converter.convert(content, msg.topic)
            self.logger.info("Result = " + str(result))
            if result:
                self.producer.send(
                    self.topic,
                    value=json.dumps(result).encode('utf-8'),
                    key=json.dumps(self.device_id).encode('utf-8'))
                self.producer.flush()
                self.statistics['MessagesSent'] += 1
        except KafkaTimeoutError as timeout_err:
            self.logger.error(f'Kafka broker timeout, {timeout_err}')

    def start(self):
        """ Main function of the mqtt producer.

        :return: None
        """
        try:
            while not self.terminated:
                if not self.connected:
                    self.__connect()
                    self._client.loop_start()
                    self.logger.info("Loop status: started")
            print("Shutdown of MQTT producer complete.", flush=True)
        except RuntimeError as run_err:
            if str(run_err) != 'Mqtt Client unavailable!':
                self.logger.error(f'RunErr: {run_err} in start')
        except Exception as error:
            self.logger.error(f'Error: {error} in start')
        finally:
            if self.connected:
                print("Closing MQTT client...", flush=True)
                self.__disconnect()
            if self.producer:
                print("Closing Kafka producer...", flush=True)
                self.producer.close()

    def _decode(self, message):
        try:
            if isinstance(message.payload, bytes):
                content = loads(message.payload.decode("utf-8", "ignore"))
            else:
                content = loads(message.payload)
        except JSONDecodeError:
            try:
                content = message.payload.decode("utf-8", "ignore")
            except JSONDecodeError:
                content = message.payload
        return content


if __name__ == '__main__':
    mqtt_producer = MQTTProducer()

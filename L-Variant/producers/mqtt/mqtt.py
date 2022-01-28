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
#   "mqtt_topics": "Server1/sensor1",1),("Server2/sensor2"),1), ...], #List of tuples containing topic names as well as
#        QOS levels
#   "mapping": [{
#       "topicName": "account/1994",
#       "converter": {
#           "type": "linemetrics",
#           "filter": {
#           }
#   }]
# }
import time
import json
import logging
import logging.handlers
import threading
import paho.mqtt.client as mqtt
from kafka import KafkaProducer
from simplejson import loads, JSONDecodeError
from converter.mqttConverter import Converter as Converter


class MQTTProducer(threading.Thread):
    def __init__(self):
        """
            Pull all data from the config file and initialize all major data variables to ensure
            that the program runs without problems
        :param config: dict as shown above
        """
        try:
            super().__init__()
            # LOGGING-FORMATTER
            loggingFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %('
                                                 'message)s')
            # ERROR-HANDLER
            errorhandler = logging.handlers.RotatingFileHandler('./logs/error.log', maxBytes=1024 * 1024 * 2,
                                                                backupCount=9, delay=False)
            errorhandler.setLevel(logging.WARNING)
            errorhandler.setFormatter(loggingFormatter)
            # DEBUG-HANDLER
            debughandler = logging.handlers.RotatingFileHandler('./logs/debug.log', maxBytes=1024 * 1024 * 2,
                                                                backupCount=9, delay=False)
            debughandler.setLevel(logging.DEBUG)
            debughandler.setFormatter(loggingFormatter)
            # LOGGER
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(errorhandler)
            self.logger.addHandler(debughandler)

            mode_path = r"./config/config.json"
            with open(mode_path) as json_file:
                config = json.load(json_file)
                json_file.close()
            self.config = config

            if "kafka_broker" and "sink_topic" in config:
                self.topic = config["sink_topic"]
                self.producer = KafkaProducer(bootstrap_servers=[config["kafka_broker"]])
            self.statistics = {'MessagesReceived': 0, 'MessagesSent': 0}
            self.connected = False
            self.deviceid = self.config["deviceid"]
            self._client = mqtt.Client(self.deviceid)
            if "username" in self.config["security"]:
                self._client.username_pw_set(self.config["security"]["username"],
                                             self.config["security"]["password"])
            if "cert_file" in self.config["security"]:
                self._client.tls_set(self.config["security"]["cert_file"])
            self.mqtt_broker = self.config["mqtt_broker"]
            self.mqtt_port = self.config["mqtt_port"]
            self.converter = Converter(self.config["mapping"])
            self.mqtt_topics = self.config["mqtt_topics"]
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in __init__", error)
            exit(1)
        self._client.on_message = self.on_message
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        self.status = "start"
        self.terminated = False
        self.start()

    def __connect(self):
        try:
            self._client.connect(self.mqtt_broker, self.mqtt_port)
        except Exception as error:
            self.logger.error(str(error))

    def on_connect(self, client, userdata, flags, rc):
        try:
            self.connected = True
            self.logger.info("Connected to MQTT broker")
            self._client.subscribe(self.mqtt_topics)
            self.logger.info("Subscribed to topic " + self.mqtt_topics)
        except Exception as error:
            self.logger.error(str(error))

    def __disconnect(self):
        try:
            self._client.loop_stop(force=False)
            self.logger.info("Loop status: stopped")
            self._client.disconnect()
        except Exception as error:
            self.logger.error(str(error))

    def on_disconnect(self, client, userdata, rc):
        try:
            self.connected = False
            self.logger.info("Disconnected from MQTT Broker")
        except Exception as error:
            self.logger.error(str(error))

    def on_message(self, client, userdata, msg):
        try:
            self.statistics['MessagesReceived'] += 1
            self.logger.info("MQTT income=" + str(self.statistics['MessagesReceived']))
            content = self._decode(msg)
            result = self.converter.convert(content, msg.topic)
            self.logger.info("Result = " + str(result))
            if result:
                self.producer.send(
                    self.topic,
                    value=json.dumps(result).encode('utf-8'),
                    key=json.dumps(self.deviceid).encode('utf-8'))
                self.producer.flush()
                self.statistics['MessagesSent'] += 1
        except Exception as error:
            self.logger.error(str(error))

    def run(self):
        try:
            while not self.terminated:
                while self.status == "start":
                    if not self.connected:
                        self.__connect()
                        self._client.loop_start()
                        self.logger.info("Loop status: started")
                    time.sleep(10)
                if self.connected:
                    self.__disconnect()
                time.sleep(1)
        except Exception as error:
            self.logger.error(str(error))

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
    producer = MQTTProducer()


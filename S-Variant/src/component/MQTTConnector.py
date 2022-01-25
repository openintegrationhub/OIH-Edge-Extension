# -*- coding: utf-8 -*-
"""
Created on Wed Dec  8 16:39:20 2020

@author: AUS
"""
# {
#     'name': 'connector',
#     'config': {
#         'hostname': 'localhost',  #MQTT Broker hostname
#         'port': 1883,
#      "security": {
#                   "cert_file": "path",
#                   "username": "user",
#                   "password": "password"
#           }
#       'topics': [("Server1/sensor1",1),("Server2/sensor2"),1), ...] #List of tuples containing topic names as well as  QOS levels
#
#     }
# }


import paho.mqtt.client as mqtt
import time
from simplejson import loads, JSONDecodeError

from component.ConnectorBaseClass import ConnectorBaseClass
from converter.mqttConverter import Converter as Converter


class Connector(ConnectorBaseClass):
    def __init__(self, config, buffer):
        super().__init__(config, buffer)
        self.buffer = buffer
        self.config = config
        self.statistics = {'MessagesReceived': 0, 'MessagesSent': 0}
        self.connected = False
        self._client = mqtt.Client(self.config["clientid"])
        if "username" in self.config["security"]:
            self._client.username_pw_set(self.config["security"]["username"],
                                         self.config["security"]["password"])
        if "cert_file" in self.config["security"]:
            self._client.tls_set(self.config["security"]["cert_file"])
        self._client.on_message = self.on_message
        self._client.on_connect = self.on_connect
        self._client.on_disconnect = self.on_disconnect
        self.status = "stop"
        self.terminated = False
        self.error = None
        self.info = None
        self.converter = Converter(self.config["mapping"])
        self.start()

    def __connect(self):
        try:
            self._client.connect(self.config["host"], self.config["port"])
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:" + str(error))
            time.sleep(10)
            self.__connect()

    def on_connect(self, client, userdata, flags, rc):
        try:
            self.connected = True
            self.logger.info("Connected to MQTT broker")
            self._client.subscribe(self.config["topic"])
            self.logger.info("Subscribed to topic " + self.config["topic"])
            self.info = ("Connected to MQTT broker. Subscribed to topic \"" + self.config["topic"] + "\".")
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:" + str(error))

    def __disconnect(self):
        try:
            self._client.loop_stop(force=False)
            self.logger.info("Loop status: stopped")
            self._client.disconnect()
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:" + str(error))

    def on_disconnect(self, client, userdata, rc):
        try:
            self.connected = False
            self.info = "Disconnected from MQTT Broker"
            self.logger.info("Disconnected from MQTT Broker")
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:" + str(error))

    def on_message(self, client, userdata, msg):
        try:
            self.statistics['MessagesReceived'] += 1
            self.logger.info("MQTT income=" + str(self.statistics['MessagesReceived']))
            content = self._decode(msg)
            result = self.converter.convert(content, msg.topic)
            self.logger.info("Result = " + str(result))
            if result:
                self.buffer.fillBuffer(result)
                self.statistics['MessagesSent'] += 1
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:" + str(error))

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
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:" + str(error))

    def _decode(self,message):
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

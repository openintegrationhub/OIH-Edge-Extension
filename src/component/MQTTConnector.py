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
import threading
import logging
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
        self.loop_status ="stopped"
        self._client = mqtt.Client(self.config["clientid"]) # TO-DO: eventually set client id in config -> Client(config['client_id'])
        if "username" in self.config["security"]:
            self._client.username_pw_set(self.config["security"]["username"],
                                         self.config["security"]["password"])
        if "cert_file" in self.config["security"]:
            self._client.tls_set(self.config["security"]["cert_file"])
        self._client.on_message = self._on_message
        self.status = "stop"
        self.terminated = False
        self.error = None
        self.info = None
        self.converter = Converter(self.config["mapping"])
        self.start()

    def _on_message(self,client, userdata, msg):
        self.statistics['MessagesReceived'] += 1
        self.logger.info("MQTT income=" + str(self.statistics['MessagesReceived']))
        content = self._decode(msg)
        self.logger.info(str(content))
        result = self.converter.convert(content, msg.topic)
        self.logger.info("Result = " + str(result))
        if result:
            self.buffer.fillBuffer(result)
            self.statistics['MessagesSent'] += 1

    def run(self):
        try:
            self.__connect()
            self.info = ("Connected to MQTT broker")
            #self.logger.info("Connected to MQTT broker")
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            #self.logger.exception("ERROR:")
        self.info = (str(self._client.subscribe(self.config["topic"])) + "Subscribed to topic " + self.config["topic"])
        #self.logger.info(str(self._client.subscribe(self.config["topic"])) + "Subscribed to topic " + self.config["topic"])
        while not self.terminated:
            while self.status == "start":
                #self.info = ("status:",self.status)
                if self.status == "start":
                    #self.executor.submit(self.start_loop())
                    self.start_loop()
                    #self.startsubscription.set()
                elif self.status == "stop":
                    self.__disconnect()
                time.sleep(10)

    def __disconnect(self):
        self.info = ("Loop Status:", self.loop_status)
        if self.loop_status == "running":
            self._client.loop_stop(force=False)
            self.loop_status="stopped"
            #self.info = ("Disconnected from MQTT broker")
            #self.logger.info("Disconnected from MQTT broker")

    def __connect(self):
        self._client.connect(self.config["host"], self.config["port"])

    def start_loop(self):
        #self.info = ("Inside query. Loop Status:", self.loop_status)
        if self.loop_status=="stopped":
            self._client.loop_start()
            self.loop_status="running"

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

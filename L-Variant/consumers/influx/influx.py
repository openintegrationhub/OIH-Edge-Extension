# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: TRM
"""
# EXAMPLE CONFIG
#
# {
#   "name": "influx_consumer",
#   "kafka_broker": "",
#   "source_topic": "",
#   "influx_host": "localhost",
#   "influx_port": "8086",
#   "influx_db": "zuPro",
#   "influx_measurement": "opcua_ema-tec",
#   "influx_username": "admin",
#   "influx_password": "admin"
# }
import ast
import json
import logging
import logging.handlers
import threading
import influxdb
from kafka import KafkaConsumer


class InfluxConsumer:
    def __init__(self):
        """
            Pull all data from the config file and initialize all major data variables to ensure
            that the program runs without problems
        :param config: dict as shown above
        """
        try:
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
            self.kafka_broker = config['kafka_broker']
            self.source_topic = config["source_topic"]
            self.influx_host = config['influx_host']
            self.influx_port = config['influx_port']
            self.influx_db = config['influx_db']
            self.influx_measurement = config['influx_measurement']
            self.influx_username = config['influx_username']
            self.influx_password = config['influx_password']
            self.consumer = KafkaConsumer(
                    self.source_topic,
                    group_id='influx_group',
                    bootstrap_servers=[self.kafka_broker],
                    auto_offset_reset='earliest'
            )
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in __init__", error)
        self.client = None
        self.data = {}
        self.info = None
        self.terminated = False
        self.error = None
        self.status = "start"
        self.start()

    def start(self):
        """
            This functions sole purpose is to start the
            programm as specified in the config.
        :return:
        """
        try:
            #self.consumer.subscribe([self.source_topic])
            if self.client is None:
                self.client = self.connect_to_influx()
            while not self.terminated:
                while self.status == "start":
                    for msg in self.consumer:
                        self.write_to_db(msg.value)
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))

    def connect_to_influx(self):
        client = None
        try:
            client = influxdb.InfluxDBClient(host=self.influx_host,
                                             port=self.influx_port,
                                             username=self.influx_username,
                                             password=self.influx_password,
                                             database=self.influx_db)
            client.create_database(self.influx_db)
            self.logger.debug('Connected to Influx-Server')
        except (ValueError, Exception):
            self.logger.error('Error: Influx-Server not connected or wrong credentials')
        return client

    def consume(self, consumer, timeout):
        try:
            while True:
                message = consumer.poll(timeout)
                if message is None:
                    continue
                yield message
            consumer.close()
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))

    def write_to_db(self, msg):
        try:
            self.logger.debug(self.client.write_points(self.json_to_points(json.loads(msg))))
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))

    def json_to_points(self, json_body):
        points = []
        try:
            for device in json_body['data']:
                for field in json_body['data'][device]:
                    point = {
                        "measurement": self.influx_measurement,
                        "tags": self.map_tags(json_body['metadata'], device),
                        "time": field['timestamp'],
                        "fields": {
                            device: field['value']}
                    }
                    points.append(point)
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))
        return points

    def map_tags(self, metadata, device):
        try:
            tags = {}
            if 'mapper' in self.config and self.config['mapper'] == 'linemetrics':
                for providerName,value in metadata.items():
                    if device in value['dataStreams'].keys():
                        tags = {'location': value['location'], 'provider': providerName}
                        break
            return tags
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))


if __name__ == '__main__':
    influx_consumer = InfluxConsumer()

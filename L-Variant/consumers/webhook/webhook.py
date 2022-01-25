# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: TRM
"""
# EXAMPLE CONFIG
#
# {
#   "name": "webhook_consumer",
#   "kafka_broker": "",
#   "source_topic": "",
#   "webhook_url": "localhost"
# }
import ast
import json
import logging
import logging.handlers
import threading
import influxdb
import requests
from confluent_kafka import Consumer


class WebhookConsumer(threading.Thread):
    def __init__(self):
        """
            Pull all data from the config file and initialize all major data variables to ensure
            that the program runs without problems
        :param config: dict as shown above
        """
        super().__init__(name="WebhookConsumer")
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
            self.webhook_url = config['webhook_url']
            self.consumer = Consumer(
                {
                    'bootstrap.servers': self.kafka_broker,
                    'group.id': 'webhook_group',
                    'auto.offset.reset': 'earliest',
                }
            )
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in __init__", error)
        self.client = None
        self.info = None
        self.terminated = False
        self.error = None
        self.status = "start"
        self.start()

    def run(self):
        """
            This functions sole purpose is to start the
            programm as specified in the config.
        :return:
        """
        try:
            self.consumer.subscribe([self.source_topic])
            while not self.terminated:
                while self.status == "start":
                    for msg in self.consume(self.consumer, 1.0):
                        json_data = {"data": json.loads(msg.value())["data"],
                                     "metadata": json.loads(msg.value())["metadata"]}
                        response = requests.post(url=self.webhook_url, json=json_data)
                        self.logger.info(response)
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))

    def consume(self, consumer, timeout):
        try:
            while True:
                message = consumer.poll(timeout)
                if message is None:
                    continue
                if message.error():
                    self.logger.error("Consumer error: {}".format(message.error()))
                    continue
                yield message
            consumer.close()
        except Exception as error:
            self.logger.error(str(self.__class__) + ": " + str(error))


if __name__ == '__main__':
    webhook_consumer = WebhookConsumer()

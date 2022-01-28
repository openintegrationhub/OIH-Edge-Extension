# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: TRM
"""
# EXAMPLE CONFIG
#
# {
# 	"name": "mongodb_consumer",
#    	"kafka_broker": "localhost:9092",
#    	"source_topic": "mqtt",
#    	"mongodb_host": "localhost",
#    	"mongodb_port": "27017",
# 	"mongodb_username": "root",
# 	"mongodb_password": "rootpassword",
# 	"mongo_db": "mqtt",
# 	"mongodb_collection": "linemetrics"
# }
import json
import logging
import logging.handlers
import pymongo
from kafka import KafkaConsumer


class MongoDBConsumer:
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
            self.mongodb_host = config['mongodb_host']
            self.mongodb_port = config['mongodb_port']
            self.username = config['mongodb_username']
            self.password = config['mongodb_password']
            self.mongo_db = config['mongo_db']
            self.mongodb_collection = config['mongodb_collection']
            self.consumer = KafkaConsumer(
                    self.source_topic,
                    group_id='mongodb_group',
                    bootstrap_servers=[self.kafka_broker],
                    auto_offset_reset='earliest'
            )
        except Exception as error:
            self.logger.error(str(error))
        self.terminated = False
        self.status = "start"
        self.mongodb_client = None
        self.start()

    def start(self):
        """
            This functions sole purpose is to start the
            programm as specified in the config.
        :return:
        """
        try:
            if self.mongodb_client is None:
                self.mongodb_client = self.connect_to_mongodb()
            while not self.terminated:
                while self.status == "start":
                    for msg in self.consumer:
                        self.write_to_db(msg.value)
        except Exception as error:
            self.logger.error(str(error))

    def consume(self, consumer, timeout):
        try:
            while True:
                message = consumer.poll(timeout)
                if message is None:
                    continue
                yield message
            consumer.close()
        except Exception as error:
            self.logger.error(str(error))

    def connect_to_mongodb(self):
        client = None
        try:
            client = pymongo.MongoClient('mongodb://{}:{}@{}:{}/'.format(self.username, self.password, self.mongodb_host,
                                                                                      self.mongodb_port))[self.mongo_db][self.mongodb_collection]
            self.logger.info("Connected to MongoDB-Server")
        except (ValueError, Exception) as error:
            self.logger.error(str(error))
        return client

    def dot_replacer(self, data):
        result = {'metadata': data['metadata'], 'data': {
        }}
        for sensor in data['data']:
            if str(sensor).__contains__("."):
                newsensor = str(sensor).replace(".", "-")
            else:
                newsensor = str(sensor)
            result['data'][newsensor] = []
            for valueset in data['data'][sensor]:
                result['data'][newsensor].append(valueset)
        return result

    def write_to_db(self, data):
        try:
            newdata = self.dot_replacer(json.loads(data))
            self.mongodb_client.insert_one(newdata)
        except (TypeError, Exception) as error:
            self.logger.error(str(error))
        return data


if __name__ == '__main__':
    consumer = MongoDBConsumer()

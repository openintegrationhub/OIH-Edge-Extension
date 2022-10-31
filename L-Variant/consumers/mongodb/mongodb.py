# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: TRM
"""
# EXAMPLE CONFIG
#
# {
# 	"name": "mongodb_consumer",
#   "kafka_broker": "localhost:9092",
#   "source_topic": "kafka_sink_component_test",
#   "mongodb_host": "localhost",
#   "mongodb_port": "27017",
# 	"mongodb_username": "root",
# 	"mongodb_password": "rootpassword",
# 	"mongo_db": "mongodb_consumer_database",
# 	"mongodb_collection": "mongodb_consumer_collection"
# }
import json

import pymongo
from component_base_class.component_base_class import ComponentBaseClass
from kafka import KafkaConsumer
from pymongo.errors import CollectionInvalid
from pymongo.errors import ConnectionFailure


class MongoDBConsumer(ComponentBaseClass):
    def __init__(self):
        """
            Pull all data from the config file and initialize all major data
            variables to ensure
            that the program runs without problems
        """
        try:
            super().__init__()
        except Exception as error:
            print(f'Failure in Base Class, {error}')
        config_template = {
            'name': '',
            'kafka_broker': '',
            "source_topic": "",
            "mongodb_host": "",
            "mongodb_port": "",
            "mongodb_username": "",
            "mongodb_password": "",
            "mongo_db": "",
            "mongodb_collection": "",
            "direct_connection": ""
        }
        # LOGGER
        self.logger = self.get_logger()
        self.config = {}
        self.kafka_broker = ''
        self.source_topic = ''
        self.mongodb_host = ''
        self.mongodb_port = ''
        self.username = ''
        self.password = ''
        self.mongo_db = ''
        self.mongodb_collection = ''
        self.unstored_data = 0
        self.direct_con = None
        self.consumer = None
        self.mongodb_client = None
        self.load_config(config_template)
        if not self.terminated:
            self.start()

    def load_config(self, config_template: dict = None, source='file'):
        """ Loads the config for the component, either from env variables
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
                self.kafka_broker = config['kafka_broker']
                self.source_topic = config["source_topic"]
                self.mongodb_host = config['mongodb_host']
                self.mongodb_port = config['mongodb_port']
                self.username = config['mongodb_username']
                self.password = config['mongodb_password']
                self.mongo_db = config['mongo_db']
                self.mongodb_collection = config['mongodb_collection']
                self.direct_con = config['direct_connection']
                if (len(self.source_topic) and len(self.kafka_broker)) > 0:
                    self.consumer = KafkaConsumer(
                        self.source_topic,
                        group_id='mongodb_group',
                        bootstrap_servers=[self.kafka_broker],
                        auto_offset_reset='earliest',
                        consumer_timeout_ms=5000
                    )
            else:
                self.logger.error('Missing key(s) in config')
                print('Missing key(s) in config', flush=True)
                self.terminated = True
                return
        except Exception as error:
            self.logger.error(f'Error: {error} in load_config')
            self.terminated = True

    def start(self):
        """ Main function of the mongodb Consumer

        :return: None
        """
        try:
            while not self.terminated:
                for msg in self.consumer:
                    if not self.mongodb_client:
                        self.mongodb_client = self.connect_to_mongodb()
                    else:
                        self.write_to_db(msg.value)
                    if self.terminated:
                        break
        except RuntimeError as run_err:
            if str(run_err) != 'MongoDB Client unavailable':
                self.logger.error(f'RunErr: {run_err} in start')
        except Exception as error:
            self.logger.error(f'Error: {error} in start')
        finally:
            print("Closing MongoDB client...", flush=True)
            if self.mongodb_client:
                self.mongodb_client.close()
            print('Closing Consumer...')
            if self.consumer:
                self.consumer.close()
        print("Shutdown of MongoDB consumer complete.", flush=True)

    def consume(self, consumer: KafkaConsumer, timeout: int):
        """ Consumes msgs of a Kafka topic.

        :param consumer: Kafka consumer.
        :param timeout: timeout timer.
        """
        while not self.terminated:
            message = consumer.poll(timeout)
            if message is None:
                continue
            yield message

    def connect_to_mongodb(self):
        """ Connects the mongodb client to the database.

        :return: None
        """
        client = None
        try:
            connection_string = 'mongodb://'
            if self.username and self.password:
                connection_string += f'{self.username}:{self.password}@'
            connection_string += f'{self.mongodb_host}:{self.mongodb_port}'
            client = pymongo.MongoClient(connection_string,
                                         directConnection=bool(
                                             self.direct_con))[
                self.mongo_db][
                self.mongodb_collection]
            self.logger.info("Connected to MongoDB-Server")
        except CollectionInvalid as col_inv:
            self.logger.error(f'Invalid Collection, {col_inv}')
            raise RuntimeError('MongoDB Client unavailable') from col_inv
        except ConnectionFailure as con_fail:
            self.logger.error(f'Connection failure, {con_fail}')
            raise RuntimeError('MongoDB Client unavailable') from con_fail
        except ValueError as val_error:
            self.logger.error(f'Invalid Credentials, {val_error}')
            raise RuntimeError('MongoDB Client unavailable') from val_error
        return client

    def dot_replacer(self, data: dict) -> dict:
        """ Replaces '.' in sensor names with '-'.

        :param data: given data
        :return: data without '.'
        """
        if 'metadata' in data:
            result = {'metadata': data['metadata'], 'data': {}}
        else:
            result = {'metadata': '', 'data': {}}
        for sensor in data['data']:
            try:
                if str(sensor).__contains__("."):
                    new_sensor = str(sensor).replace(".", "-")
                else:
                    new_sensor = str(sensor)
                result['data'][new_sensor] = []
                for valueset in data['data'][sensor]:
                    result['data'][new_sensor].append(valueset)
            except KeyError as key_err:
                self.unstored_data += 1
                self.logger.warning(f'Data not in the right format.'
                                    f'Unstored: {self.unstored_data}')
                self.logger.error(key_err)
                continue
        return result

    def write_to_db(self, data):
        """ Write the given data into the database

        :param data: Given data
        :return: data
        """
        try:
            new_data = self.dot_replacer(json.loads(data))
            self.mongodb_client.insert_one(new_data)
        except json.JSONDecodeError as decode_err:
            self.logger.warning(f'Could not decode message.'
                                f'Unstored: {self.unstored_data}')
            self.logger.error(decode_err)
        return data


if __name__ == '__main__':
    mongo_consumer = MongoDBConsumer()

# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: TRM
"""
# EXAMPLE CONFIG
#
# {
#   "name": "webhook_consumer",
#   "kafka_broker": "localhost:9092",
#   "source_topic": "kafka_sink_component_test",
#   "webhook_url": "https://webhook.site/test"
# }
import json
from json import JSONDecodeError

import requests
from component_base_class.component_base_class import ComponentBaseClass
from kafka import KafkaConsumer


class WebhookConsumer(ComponentBaseClass):
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
            "name": "",
            "kafka_broker": "",
            "source_topic": "",
            "webhook_url": ""
        }
        # LOGGER
        self.logger = self.get_logger()
        self.config = {}
        self.kafka_broker = ''
        self.source_topic = ''
        self.webhook_url = ''
        self.unstored_data = 0
        self.consumer = None
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
        if self.config or source != 'file':
            config = self.get_config(
                config_template,
                source=source,
                file_path=f'/config/{self.path_name}'
            )
        else:
            config = self.wait_for_config_insertion()
        self.config = config
        try:
            if self.config and all(key in self.config
                                   for key in config_template.keys()):
                self.kafka_broker = config['kafka_broker']
                self.source_topic = config["source_topic"]
                self.webhook_url = config['webhook_url']
                if (len(self.source_topic) and len(self.kafka_broker)) > 0:
                    self.consumer = KafkaConsumer(
                        self.source_topic,
                        group_id='webhook_group',
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
        """ Main function of the webhook consumer.

        :return: None
        """
        try:
            while not self.terminated:
                for msg in self.consumer:
                    try:
                        json_data = {"data": json.loads(msg.value())["data"],
                                     "metadata": json.loads(msg.value())[
                                         "metadata"]}
                        response = requests.post(url=self.webhook_url,
                                                 json=json_data)
                        if not response.ok:
                            self.logger.error(
                                "Error sending request. Response code: " + str(
                                    response.status_code))
                    except JSONDecodeError as decode_err:
                        self.unstored_data += 1
                        self.logger.warning(f'Could not decode message.'
                                            f'Unstored: {self.unstored_data}')
                        self.logger.error(decode_err)
                        continue
        except Exception as error:
            self.logger.error(f'Error: {error} in start')
        finally:
            print('Closing Consumer...')
            if self.consumer:
                self.consumer.close()

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


if __name__ == '__main__':
    webhook_consumer = WebhookConsumer()

# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: TRM
"""
import json
# EXAMPLE CONFIG
#
# {
#   "name": "influx_consumer",
#   "kafka_broker": "localhost:19092",
#   "source_topic": "kafka_sink_component_test",
#   "influx_host": "localhost",
#   "influx_port": "8086",
#   "influx_db": "influx_consumer_database",
#   "influx_measurement": "influx_consumer_measurement",
#   "influx_username": "admin",
#   "influx_password": "admin"
#   "influx_schema": [{
#       "value_pos": [],
#       "timestamp_pos": [],
#       "metadata_pos": [],
#       "field_name": ""
#   }]
# }
from datetime import datetime
from socket import error as SocketError
from typing import Union

import influxdb
import kafka.errors
from component_base_class.component_base_class import ComponentBaseClass
from kafka import KafkaConsumer
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import NewConnectionError


class InfluxConsumer(ComponentBaseClass):
    """ This class function as a consumer, which consumes data
    of a Kafka topic and writes it into an influxdb.
    """

    def __init__(self):
        """
            Pull all data from the config file or environment variables and
            initialize all major data variables to ensure program stability.
        """
        super().__init__()
        config_template = {
            "name": "",
            "kafka_broker": "",
            "source_topic": "",
            "influx_port": "",
            "influx_host": "",
            "influx_db": "",
            "influx_schema": "",
            "influx_measurement": "",
            "influx_username": "",
            "influx_password": ""
        }
        self.logger = self.get_logger()
        self.config = {}
        self.kafka_broker = ''
        self.source_topic = ''
        self.influx_port = ''
        self.influx_host = ''
        self.influx_db = ''
        self.influx_measurement = ''
        self.influx_username = ''
        self.influx_password = ''
        self.unstored = 0
        self.influx_schema = {}
        self.client = None
        self.consumer = None
        self.load_config(config_template)
        self.client = None
        self.data = {}
        if not self.terminated:
            self.start()

    def load_config(self, config_template: dict = None, source='file'):
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
                self.kafka_broker = config['kafka_broker']
                self.source_topic = config["source_topic"]
                self.influx_host = config['influx_host']
                self.influx_port = config['influx_port']
                self.influx_db = config['influx_db']
                self.influx_measurement = config['influx_measurement']
                self.influx_username = config['influx_username']
                self.influx_password = config['influx_password']
                self.influx_schema = config['influx_schema']
                if (len(self.source_topic) and len(self.kafka_broker)) > 0:
                    self.consumer = KafkaConsumer(
                        self.source_topic,
                        group_id='influx_group',
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
        """ Main function of the influx consumer.

        :return: None
        """
        try:
            while not self.terminated:
                for msg in self.consumer:
                    if not self.client:
                        self.client = self.connect_to_influx()
                    else:
                        self.write_to_db(msg.value)
                    if self.terminated:
                        break
        except RuntimeError as run_err:
            if str(run_err) != 'Influx Client unavailable':
                self.logger.error(f'RunErr: {run_err} in start')
        except Exception as error:
            self.logger.error(f'Error: {error} in start')
        finally:
            print("Closing Influx client...", flush=True)
            if self.client:
                self.client.close()
            print('Closing Consumer')
            if self.consumer:
                self.consumer.close()
        print("Shutdown of Influx consumer complete.", flush=True)

    def connect_to_influx(self):
        """ Connects the influx client to the database

        :return: influx client
        """
        client = None
        try:
            client = influxdb.InfluxDBClient(
                host=self.influx_host,
                port=self.influx_port,
                username=self.influx_username,
                password=self.influx_password,
                database=self.influx_db)
            client.create_database(self.influx_db)
            self.logger.debug('Connected to Influx-Server')
            print('Connected to Influx-Server')
        except ValueError as val_err:
            self.logger.error(f'Invalid credentials, {val_err}')
            raise RuntimeError('Influx Client unavailable') from val_err
        except (NewConnectionError, MaxRetryError,
                ConnectionError, SocketError) as con_ref_err:
            self.logger.error(f'Influx-Server connection refused, '
                              f'{con_ref_err}')
            raise RuntimeError('Influx Client unavailable') from con_ref_err
        return client

    def consume(self, consumer: KafkaConsumer, timeout: int):
        """ Consumes msgs of a Kafka topic.

        :param consumer: Kafka consumer.
        :param timeout: timeout timer.
        """
        try:
            while not self.terminated:
                message = consumer.poll(timeout)
                if message is None:
                    continue
                yield message
        except kafka.errors.KafkaTimeoutError as timeout_err:
            self.logger.error(f'Kafka broker timeout, {timeout_err}')

    def write_to_db(self, msg):
        """ Writes the converted data into the db

        :param msg: Kafka message.
        """
        try:
            if self.influx_schema:
                self.client.write_points(
                    self.json_to_points_mapper(json.loads(msg)))
            else:
                self.client.write_points(self.json_to_points(json.loads(msg)))
        except json.JSONDecodeError as decode_err:
            self.unstored += 1
            self.logger.warning(f'Could not decode message.'
                                f'Unstored: {self.unstored}')
            self.logger.error(decode_err)

    def json_to_points(self, json_body: dict) -> list:
        """This method is used if there is no influx_schema given and uses the
        standard procedure to write the data into the influx db.

        :param json_body: given data.
        :return: points to write into the influx.
        """
        points = []
        for device in json_body['data']:
            try:
                for field in json_body['data'][device]:
                    point = {
                        "measurement": self.influx_measurement,
                        "tags": self.map_tags(json_body['metadata'], device),
                        "time": field['timestamp'],
                        "fields": {
                            device: field['value']}
                    }
                    points.append(point)
            except KeyError as key_err:
                self.unstored += 1
                self.logger.warning(f'Incoming data not in the right format.'
                                    f'Might want to consider using schema '
                                    f'function. Unstored: {self.unstored}')
                self.logger.error(key_err)
                continue
        return points

    def json_to_points_mapper(self, json_body: dict) -> list:
        """ This method converts the given data into points, which can be
        inserted into the influxdb

        :param json_body: data dict.
        :return: points to be inserted into the db.
        """
        points = []
        for influx_schema in self.influx_schema:
            try:
                if "meta_path" in self.config:
                    metadata = self.get_value(json_body,
                                              self.config['meta_path'])
                else:
                    metadata = []
                if "data_path" in influx_schema:
                    json_body = self.get_value(json_body,
                                               influx_schema['data_path'])
                if "name_pos" in influx_schema and "name" in influx_schema:
                    values = self.get_value(json_body,
                                            influx_schema['value_pos'],
                                            influx_schema['name_pos'],
                                            influx_schema['name'])
                    timestamps = self.get_value(json_body,
                                                influx_schema['timestamp_pos'],
                                                influx_schema['name_pos'],
                                                influx_schema['name'])
                    if not metadata:
                        metadata = self.get_value(json_body,
                                                  influx_schema[
                                                      'metadata_pos'],
                                                  influx_schema['name_pos'],
                                                  influx_schema['name'])
                else:
                    values = self.get_value(json_body,
                                            influx_schema['value_pos'])
                    timestamps = self.get_value(json_body,
                                                influx_schema['timestamp_pos'])
                    if not metadata:
                        metadata = self.get_value(json_body,
                                                  influx_schema[
                                                      'metadata_pos'])
                for i in range(len(values)):
                    if isinstance(values[i], list) and isinstance(
                            timestamps[i], list):
                        for j in range(len(values[i])):
                            if len(values[i]) == len(timestamps[i]):
                                points.append(self.create_point(
                                    timestamps[i][j],
                                    influx_schema['field_name'],
                                    values[i][j],
                                    metadata, i))
                            else:
                                points.append(
                                    self.create_point(
                                        timestamps[i],
                                        influx_schema['field_name'],
                                        values[i][j],
                                        metadata, i))
                    elif isinstance(values[i], list):
                        for j in range(len(values[i])):
                            points.append(
                                self.create_point(
                                    timestamps[i],
                                    influx_schema['field_name'],
                                    values[i][j],
                                    metadata, i))
                    else:
                        points.append(
                            self.create_point(
                                timestamps[i],
                                influx_schema['field_name'],
                                values[i],
                                metadata, i))
            except KeyError as key_err:
                self.unstored += 1
                self.logger.warning(f'Mapping Error.'
                                    f'Unstored: {key_err}')
                self.logger.error(key_err)
                continue
        return points

    def create_point(self,
                     timestamp: Union[datetime.timestamp, Union[float, int]],
                     field_name: str,
                     val: float,
                     metadata: list,
                     meta_pos: int) -> dict:
        """This function generates a point for the
        influxdb, regarding the given data.

        :param meta_pos: position of the metadata.
        :param timestamp: timestamp of current data
        :param field_name: field name given in the config
        :param val: current value
        :param metadata: metadata of the given value
        :return: point
        """
        if isinstance(timestamp, (float, int)):
            return {
                "measurement": "test",
                "tags": {},
                "time": datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"),
                "metadata": metadata,
                "fields": {
                    field_name: val
                }
            }
        else:
            return {
                "measurement": "test",
                "tags": {},
                "time": timestamp,
                "metadata": self.map_tags(metadata, field_name, meta_pos),
                "fields": {
                    field_name: val
                }
            }

    def get_value(self,
                  data: Union[dict, list],
                  influx_schema: list,
                  name_pos: list = None,
                  field_name: str = "") -> Union[list, None]:
        """ This method is used to get certain data fields out of a nested
        dictionary.

        :param field_name: optional, if the given data consists of lists
        with multiple names, which are not fetchable with the normal method.
        :param name_pos: optional, position of the field name
        :param data: nested dict.
        :param influx_schema: list which functions as a path to the data field.
        :return: list with the content of the data field.
        """
        values = []
        if isinstance(data, list):
            if len(influx_schema) == 0:
                values.append(data)
            else:
                for field in data:
                    value_list = self.get_value(
                        field,
                        influx_schema,
                        name_pos,
                        field_name)
                    if value_list:
                        for value in value_list:
                            values.append(value)
                    else:
                        continue
        else:
            if not name_pos:
                i = 0
                data_fields = data
                for field in influx_schema:
                    i += 1
                    if isinstance(field, list):
                        d_field = []
                        for val_field in field:
                            d_field.append(data_fields[val_field])
                        data_fields = d_field
                    else:
                        if field in data_fields:
                            data_fields = data_fields[field]
                            if isinstance(data_fields, list):
                                return self.get_value(
                                    data_fields,
                                    influx_schema[i:])
                        else:
                            return
                values.append(data_fields)
            else:
                name = self.get_value(data, name_pos)
                if name[0] == field_name:
                    return self.get_value(data, influx_schema)
        return values

    def map_tags(self,
                 metadata: list,
                 device: str,
                 meta_pos: int = 0) -> dict:
        """ This method maps the metadata tags as specified in the config.

        :param meta_pos: position of the metadata.
        :param metadata: dict with metadata.
        :param device: device name.
        :return: mapped tags.
        """
        tags = {}
        if 'mapper' in self.config \
                and self.config['mapper'] == 'linemetrics':
            if self.influx_schema:
                iterator = metadata[meta_pos]
            else:
                iterator = metadata
            for provider_name, value in iterator.items():
                if device in value['dataStreams'].keys():
                    tags = {'location': value['location'],
                            'provider': provider_name}
                    break
        else:
            # Currently no use case.
            pass
        return tags


if __name__ == '__main__':
    influx_consumer = InfluxConsumer()

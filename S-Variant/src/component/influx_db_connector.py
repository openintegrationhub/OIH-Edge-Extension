# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 10:49:49 2020
"""

__author__ = "AUS"

from influxdb import InfluxDBClient

from component.component_base_class import ComponentBaseClass


class InfluxConnector(ComponentBaseClass):
    """
    This class connects to an influxdb and writes the incoming data into the
    database.

    Attributes:
    -----------
        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

        host (str): In the config specified host to connect to.

        port (str): In the config specified port to connect the influx.

        username (str): In the config specified username to connect to.

        password (str): In the config specified password of the user.

        database (str): In the config specified database to connect to and
        write into.

        measurement (str): Measurement to be written into.

        client (InfluxDBClient): client object, which's function is to write
        the data into the database.

    Methods:
    --------
        connect_to_influx(): This method connects the InfluxDBClient to the
        influxdb and creates a database as specified in the config.

        json_to_points(json_body: dict): This method converts the given data
        into points which can be written into an influxdb.

        map_tags(metadata: dict, device: str): This method maps the metadata
        of the given data to tags of the influxdb.

        process(): This method processes the incoming data and returns it
        unchanged.
    """
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration.
        """
        super().__init__(config)
        self.host = config['host']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.database = config['db']
        self.measurement = config['measurement']
        self.error = None
        self.info = None
        self.client = None
        self.connect_to_influx()

    def connect_to_influx(self):
        """This method connects the InfluxDBClient to the influxdb and creates
        a database as specified in the config.
        """
        try:
            self.client = InfluxDBClient(host=self.host,
                                         port=self.port,
                                         username=self.username,
                                         password=self.password)
            self.client.create_database(self.database)
            self.client.switch_database(self.database)
            self.info = 'Connected to Influx-Server'
            self.logger.info('Connected to Influx-Server')
        except (ValueError, Exception):
            self.error = 'Error: Influx-Server not connected or wrong ' \
                         'credentials'
            self.logger.exception("ERROR:")

    def json_to_points(self, json_body: dict) -> list:
        """This method converts the given data into points which can be written
        into an influxdb.
        """
        points = []
        try:

            for device in json_body['data']:
                for field in json_body['data'][device]:
                    point = {
                        "measurement": self.measurement,
                        "tags": self.map_tags(json_body['metadata'], device),
                        "time": field['timestamp'],
                        "fields": {
                            device: float(field['value'])}
                    }
                    points.append(point)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
        return points

    def map_tags(self, metadata: dict, device: str):
        """This method maps the metadata of the given data to tags of the
        influxdb.

        Parameters:
        -----------
        metadata (dict): Metadata of the incoming data.

        device (str): Name of the device.
        """
        tags = {}

        if self.config['mapper'] == 'linemetrics':
            for provider_name, value in metadata.items():
                if device in value['dataStreams'].keys():
                    tags = {'location': value['location'],
                            'provider': provider_name}
                    break
        elif self.config['mapper'] == "zuPro":
            tags = metadata
        return tags

    def process(self, data: dict) -> dict:
        """This method processes the incoming data and returns it unchanged."""
        try:
            points = self.json_to_points(data)
            self.logger.debug(f"RESULT JSON_TO_POINTS = {str(points)}")
            self.logger.debug(f"RESULT CLIENTWRITE = "
                              f"{str(self.client.write_points(points))}")
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
        return data

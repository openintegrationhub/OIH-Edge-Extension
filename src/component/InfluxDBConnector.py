# -*- coding: utf-8 -*-
"""
Created on Thu Nov  5 10:49:49 2020

@author: AUS
"""
from component.ComponentBaseClass import ComponentBaseClass
from influxdb import InfluxDBClient


class InfluxConnector(ComponentBaseClass):
    def __init__(self, config):
        super().__init__(config)
        self.host = config['host']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.db = config['db']
        self.measurement = config['measurement']
        self.error = None
        self.info = None
        self.client = None
        self.connectToInflux()

    def connectToInflux(self):
        try:
            self.client = InfluxDBClient(host=self.host, port=self.port, username=self.username, password=self.password)
            self.client.create_database(self.db)
            self.client.switch_database(self.db)
            self.info = 'Connected to Influx-Server'
            self.logger.info('Connected to Influx-Server')
        except (ValueError, Exception):
            self.error = 'Error: Influx-Server not connected or wrong credentials'
            self.logger.exception("ERROR:")

    def json_to_points(self, json_body):
        try:
            points = []

            for device in json_body['data']:
                for field in json_body['data'][device]:
                    point = {
                            "measurement": self.measurement,
                            #"tags": json_body['metadata'],
                            "tags": self.map_tags(json_body['metadata'],device),
                            "time": field['timestamp'],
                            "fields": {
                                device: field['value']}
                            }
                    points.append(point)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
        return points

    def map_tags(self,metadata,device):
        tags={}
        if self.config['mapper'] == 'linemetrics':
            for providerName,value in metadata.items():
                if device in value['dataStreams'].keys():
                    tags = {'location': value['location'], 'provider': providerName}
                    break
        return tags


    def process(self, data):
        try:
            self.client.write_points(self.json_to_points(data))
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
        return data

        
    
    
        
        
    

    
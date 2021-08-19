# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 08:09:23 2020

@author: AUS
"""

import datetime
import time
import random
from component.ConnectorBaseClass import ConnectorBaseClass

# Example config structure
# 'config': {
#
#     'sensors': ["sensor1", "sensor2"]
#     'randomrange': (1,10)
#     'period': 2              #creates new data in a 2 second period 
 

class Connector(ConnectorBaseClass):
    def __init__(self, config, buffer):
        super().__init__(config, buffer)
        self.buffer = buffer
        self.sensors = config['sensors']
        self.thresh=config['randomrange']
        self.period=config['period']
        self.data = ""
        self.status = "stop"
        self.terminated = False
        self.error = None
        self.info = None
        self.start()

    def run(self):
        self.info = "DemoConnector started"
        self.logger.info("DemoConnector started")
        while not self.terminated:
            while self.status == "start":
                self.query()
        self.logger.info("DemoConnector stopped")
        self.status = "stop"

    def query(self):
        try:
            self.data = {
                'metadata': {
                    
                },
                'data': {
                }
            }
            for sensor in self.sensors:
                self.data['data'][sensor] = []
                valueset = {'timestamp': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                            'value': random.uniform(self.thresh[0],self.thresh[1])}
                self.data['data'][sensor].append(valueset)
            time.sleep(self.period)
            self.buffer.fillBuffer(self.data)
        except (ValueError, Exception) as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")



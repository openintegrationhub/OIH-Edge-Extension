# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Component of the On-Edge Adapter.
"""

from abc import ABC, abstractmethod
import logging
import threading

from component.buffer import Buffer


class ConnectorBaseClass(ABC, threading.Thread):
    """This class is used as super class of all connectors.

    Attributes:
    -----------
        buffer (buffer): Stores the incoming data.

        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

        status (str): status flag of the connector, either 'start' or 'stop'.

        terminated (bool): status flag of the flow, if True the flow is
        stopped.

    Methods:
    --------
        run(): The run() method can be used to query a data source. Write
        errors to self.error field. If self.error is not empty Main-Class
        will set self.status to 'stop'.
    """
    @abstractmethod
    # Connector is created by Main-Class and given a config and buffer object
    def __init__(self, config: dict, buffer: Buffer):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration.

            buffer (Buffer): Buffer instance in which the data of the
            connector will be stored.
        """
        super().__init__()
        self.buffer = buffer
        self.config = config
        self.error = None
        self.info = None
        self.logger = logging.getLogger()
        self.status = "stop"
        self.terminated = False

    @abstractmethod
    def run(self):
        """The run() method can be used to query a data source. Write errors
        to self.error field. If self.error is not empty Main-Class will set
        self.status to 'stop'.
        """
        # do something when Connector is started for the first time
        while not self.terminated:
            # do something while Connector has stopped but is still running
            while self.status == "start":
                # do something while Connector is running and self.status is
                # "start" i.e. query data source
                pass
        # do something when Connector has been terminated

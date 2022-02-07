# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Component of the On-Edge Adapter.
"""

import threading
import logging
import copy

from component import aggregator_timebased, aggregator, \
    anonymizer, influx_db_connector, webhook_connector, \
    pay_per_x


class EdgeOrchestrator(threading.Thread):
    """
    This class passes the data given from the buffer to the respective
    component.

    Attributes:
    -----------
        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

        flow (list): The flow contains a list of all components, which will
        be executed in order.

        data (dict): Data which will be passed from one component to another.

        buffer (buffer): Buffered data of the connectors.

        status (str): Status flag of the edge_orchestrator, either 'start' or
        'stop'.

        terminated (bool): Status flag of the flow, if True the flow is
        stopped.

        flow_position (int): Current step of the flow.

    Methods:
    --------
        analyze_config(mode: dict): This method is called when the
        edge_orchestrator is initialized, it parses the mode and builds the
        flow with the specified components. At the end all components are
        checked for errors.

        run(): This method is executed at thread start and only ends when
        terminate() is called.

        run_flow(): This method processes the flow and passes data from one
        component to the next. If a component does not return any data the
        flow starts again. If a component reports an error, the flow is
        stopped.

        error_and_info_checker(): This method checks the flow for errors or
        info messages. If a component wrote an error message, the flow will
        be stopped. If a component wrote an info message, it will be written
        into the info list and gets passed to the main.
    """
    def __init__(self, config: dict, buffer):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration.

            buffer (Buffer): Buffer instance in which the data of the
            connector will be stored.
        """
        super().__init__(name="EdgeOrchestrator")
        self.flow = None
        self.data = None
        self.logger = logging.getLogger()
        self.config = config
        self.buffer = buffer
        self.status = "stop"
        self.terminated = False
        self.errors = []
        self.info = []
        self.flow_position = 0
        self.analyze_config(self.config)
        self.start()

    def analyze_config(self, mode: dict):
        """This method is called when the edge_orchestrator is initialized, it
        parses the mode and builds the flow with the specified components.
        At the end all components are checked for errors.

        Parameters:
        -----------
            mode (dict): Given config to analyze.
        """
        self.config = mode
        if self.config is None:
            self.errors.append("EdgeOrchestrator found no mode")
            self.logger.error("EdgeOrchestrator found no mode")
            return
        else:
            self.flow = []
            self.flow.append(self.buffer)
            for step in self.config['steps']:
                if step['name'] == 'anonymizer':
                    component = anonymizer.Anonymizer(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'aggregator_ts':
                    component = aggregator_timebased.Aggregator(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'payperx':
                    component = pay_per_x.PayPerX(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'aggregator':
                    component = aggregator.Aggregator(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'influxdbconnector':
                    component = influx_db_connector.InfluxConnector(
                        step['config'])
                    self.flow.append(component)
                elif step['name'] == 'webhookconnector':
                    component = webhook_connector.WebhookConnector(
                        step['config'])
                    self.flow.append(component)
            for component in self.flow:
                if component.error is not None:
                    self.errors.append(component.error)
                    component.error = None
                if len(self.errors) != 0:
                    self.errors.append("Error in EdgeOrchestrator"
                                       " configuration")

    def run(self):
        """This method is executed at thread start and only ends when
        terminate() is called
        """
        while not self.terminated:
            self.error_and_info_checker()
            while self.status == "start":
                self.error_and_info_checker()
                self.run_flow()
        self.status = "stop"

    def run_flow(self):
        """This method processes the flow and passes data from one component to
        the next. If a component does not return any data the flow starts
        again. If a component reports an error, the flow is stopped.
        """
        try:
            self.data = self.flow[self.flow_position]\
                .process(self.data)
            if self.data is None or self.flow_position == len(self.flow) - 1:
                self.flow_position = 0
            else:
                self.flow_position += 1
        except Exception as error:
            self.status = "stop"
            self.errors.append(f"Error in Modul "
                               f"{str(self.flow[self.flow_position])} : "
                               f"{str(error)} \nDaten: {str(self.data)}")
            self.logger.exception("ERROR:")

    def error_and_info_checker(self):
        """This method checks the flow for errors or info messages. If a
        component wrote an error message, the flow will be stopped. If a
        component wrote an info message, it will be written into the info
        list and gets passed to the main.
        """
        for component in self.flow:
            if component.error is not None:
                self.status = "stop"
                self.errors.append(component.error)
                component.error = None
            if component.info is not None:
                self.info.append(component.info)
                self.logger.info(component.info)
                component.info = None

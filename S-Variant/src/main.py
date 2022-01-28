# -*- coding: utf-8 -*-
"""
main of the OIH-Edge.
"""

import threading
import json
import time
import logging
import logging.handlers

from component import edge_orchestrator, buffer
from mainconnector import connector


class Main:
    """This class function as the main of the OIH Edge.

    Attributes:
    -----------
        errors (list): stores the error messages.

        info (list): stores the info messages.

        menu_lock (threading.Lock):

        red (str): red color encoding.

        green (str): green color encoding.

        end_c (str): color encoding.

        menu_choice (int):

        config (dict): Given configuration

        buffer (obj): Contains an instance of the buffer.

        connector (obj): Contains an instance of the specified connector.
        Either OPCUA, MQTT, WEBHOOK or DEMO connector.

        edge_orchestrator (obj): Contains an instance of the edge_orchestrator

        logger (logger): logger used to write debug or error logs.

    Methods:
    --------
        error_checker(): This method is used to check if any component returned
        an error, if so stop either the edge_orchestrator or the connector.

        info_checker(): This method is used to check the info field, if it is
        not empty print the info into the console.

        get_input(): This method is used to get the user input and execute the
        input choice.

        load_config(): This method is used to reload the config. It terminates
        and re-initializes the flow.

        load_menu(): This method is used to load the menu and update it for
        every user input or every event of components.
    """
    def __init__(self):
        """Initializes the main."""
        self.errors = []
        self.info = []
        self.menu_lock = threading.Lock()
        self.red = '\033[91m'
        self.green = '\033[92m'
        self.end_c = '\033[0m'
        self.menu_choice = None
        self.config = None
        self.buffer = None
        self.connector = None
        self.edge_orchestrator = None

        # LOGGING-FORMATTER
        logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - '
                                              '%(filename)s - %(funcName)s - '
                                              '%(message)s')
        # ERROR-HANDLER
        error_handler = logging.handlers.RotatingFileHandler(
            './src/logs/error.log', maxBytes=1024 * 1024 * 2,
            backupCount=9, delay=False)
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(logging_formatter)
        # DEBUG-HANDLER
        debug_handler = logging.handlers.RotatingFileHandler(
            './src/logs/debug.log', maxBytes=1024 * 1024 * 2,
            backupCount=9, delay=False)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging_formatter)
        # LOGGER
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(debug_handler)

        ############
        mode_path = r"./src/mainconfig/config.json"
        with open(mode_path, encoding="utf-8") as json_file:
            self.config = json.load(json_file)
            json_file.close()
        if 'buffer' in self.config and 'config' in self.config['buffer']:
            self.buffer = buffer.Buffer(self.config['buffer']['config'])
        else:
            self.errors.append("Error in Buffer configuration")
        for step in self.config['steps']:
            if step['name'] == "connector":
                self.connector = connector.Connector(step['config'],
                                                     self.buffer)
        self.edge_orchestrator = edge_orchestrator.EdgeOrchestrator(
            self.config, self.buffer)
        for mode_key in ['buffer', 'steps']:
            if mode_key not in self.config.keys():
                self.errors.append(f' {mode_key} missing in Mode config')
                self.logger.error(' %s missing in Mode config', mode_key)
        ############

        # self.load_config()
        # ERROR-CHECKER-THREAD
        self.error_checker_thread = threading.Thread(target=self.error_checker,
                                                     name="Error Checker")
        self.error_checker_thread.start()
        # GET-INPUT-THREAD
        self.get_input_thread = threading.Thread(target=self.get_input,
                                                 name="Get Input")
        self.get_input_thread.start()
        while self.menu_choice != "exit":
            time.sleep(1)

    def error_checker(self):
        """This method is used to check if any component returned an error, if so
        stop either the edge_orchestrator or the connector.
        """
        error = False
        info = False
        self.info_checker()
        self.load_menu()
        try:
            while self.menu_choice != "exit":
                self.info_checker()
                if len(self.info) != 0:
                    info = True
                if len(self.errors) != 0:
                    error = True
                if self.connector.error is not None:
                    self.connector.status = "stop"
                    self.errors.append(self.connector.error)
                    self.connector.error = None
                    error = True
                if len(self.edge_orchestrator.errors) != 0:
                    self.errors += self.edge_orchestrator.errors
                    self.edge_orchestrator.errors.clear()
                    error = True
                else:
                    time.sleep(1)
                if error or info:
                    with self.menu_lock:
                        self.load_menu()
                        error = False
                        info = False
        except Exception as error:
            self.errors.append(str(self.__class__) + ": " + str(error))
            self.logger.exception("ERROR:")

    def info_checker(self):
        """This method is used to check the info field, if it is not empty
        print the info into the console.
        """
        try:
            if self.connector.info is not None:
                self.info.append(self.connector.info)
                self.connector.info = None
            if len(self.edge_orchestrator.info) != 0:
                self.info += self.edge_orchestrator.info
                self.edge_orchestrator.info.clear()
        except Exception as error:
            self.errors.append(str(self.__class__) + ": " + str(error))
            self.logger.exception("ERROR:")

    def get_input(self):
        """This method is used to get the user input and execute the input
        choice.
        """
        while self.menu_choice != "exit":
            self.menu_choice = input()
            if self.menu_choice == '1':
                if self.edge_orchestrator.status == "stop":
                    self.edge_orchestrator.status = "start"
                else:
                    self.edge_orchestrator.status = "stop"
            elif self.menu_choice == '2':
                if self.connector.status == "stop":
                    self.connector.status = "start"
                else:
                    self.connector.status = "stop"
            elif self.menu_choice == '3':
                self.info.append("Reading mode...")
                self.load_config()
            elif self.menu_choice == '4':
                self.menu_choice = "exit"
                if self.edge_orchestrator is not None:
                    self.edge_orchestrator.status = "stop"
                    self.edge_orchestrator.terminated = True
                if self.connector is not None:
                    self.connector.status = "stop"
                    self.connector.terminated = True
                print("Goodbye")
                return
            with self.menu_lock:
                self.load_menu()

    def load_config(self):
        """This method is used to reload the config. It terminates and
        re-initializes the flow.
        """
        mode_path = r"./src/mainconfig/config.json"
        try:
            with open(mode_path, encoding="utf-8") as json_file:
                self.config = json.load(json_file)
                json_file.close()
            if self.edge_orchestrator is not None:
                self.edge_orchestrator.status = "stop"
                self.edge_orchestrator.terminated = True
            if self.connector is not None:
                self.connector.status = "stop"
                self.connector.terminated = True
            time.sleep(3)
            if 'buffer' in self.config and 'config' in self.config['buffer']:
                self.buffer = buffer.Buffer(self.config['buffer']['config'])
            else:
                self.errors.append("Error in Buffer configuration")
            for step in self.config['steps']:
                if step['name'] == "connector":
                    self.connector = connector.Connector(step['config'],
                                                         self.buffer)
            self.edge_orchestrator = edge_orchestrator.EdgeOrchestrator(
                self.config, self.buffer)
            for mode_key in ['buffer', 'steps']:
                if mode_key not in self.config.keys():
                    self.errors.append(f' {mode_key} missing in Mode config')
                    self.logger.error(' %s missing in Mode config', mode_key)
        except Exception as error:
            self.errors.append(str(self.__class__) + ": " + str(error))
            self.logger.exception("ERROR:")

    def load_menu(self):
        """This method is used to load the menu and update it for
        every user input or every event of components.
        """
        print("\nWelcome to OIH Edge Interface\n")
        # Error output
        if len(self.errors) != 0 or len(self.info) != 0:
            print("##############################")
            for error in self.errors:
                print(f"{self.red}Error: {self.end_c}" + str(error))
            for info in self.info:
                print(f"{self.green}Info: {self.end_c}" + str(info))
            print("##############################\n")
            self.info.clear()
            self.errors.clear()
        # EdgeOrchestrator status
        print("EdgeOrchestrator: " +
              (f"{self.red}Stopped{self.end_c}" if (
                          self.edge_orchestrator.status == 'stop') else
               f"{self.green}Started{self.end_c}"))
        # Connector status
        print("Connector: " +
              (f"{self.red}Stopped{self.end_c}" if (
                          self.connector.status == 'stop') else
               f"{self.green}Started{self.end_c}"))
        # print menu
        print("\nWaiting for command:\n")
        print("1) Start EdgeOrchestrator" if (
                    self.edge_orchestrator.status == 'stop')
              else "1) Stop EdgeOrchestrator")
        print("2) Start Connector" if (
                    self.connector.status == 'stop') else "2) Stop Connector")
        print("3) Reload mode")
        print("4) Exit\n")
        # wait for user input


if __name__ == '__main__':
    main = Main()

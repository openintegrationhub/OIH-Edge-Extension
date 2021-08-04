from component import EdgeOrchestrator
from mainconnector import Connector
from component import Buffer
import threading
import json
import time
import logging


class Main:
    def __init__(self):
        self.errors = []
        self.info = []
        self.menu_lock = threading.Lock()
        self.red = '\033[91m'
        self.green = '\033[92m'
        self.endc = '\033[0m'
        self.menuchoice = None
        self.config = None
        self.buffer = None
        self.connector = None
        self.edgeOrchestrator = None

        # LOGGING-FORMATTER
        loggingFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
        # ERROR-HANDLER
        errorhandler = logging.FileHandler('./src/logs/error.log')
        errorhandler.setLevel(logging.WARNING)
        errorhandler.setFormatter(loggingFormatter)
        # DEBUG-HANDLER
        debughandler = logging.FileHandler('./src/logs/debug.log')
        debughandler.setLevel(logging.DEBUG)
        debughandler.setFormatter(loggingFormatter)
        # LOGGER
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(errorhandler)
        self.logger.addHandler(debughandler)

        ############
        mode_path = r"./mainconfig/config.json"
        with open(mode_path) as json_file:
            self.config = json.load(json_file)
            json_file.close()
        if 'buffer' in self.config and 'config' in self.config['buffer']:
            self.buffer = Buffer.Buffer(self.config['buffer']['config'])
        else:
            self.errors.append("Error in Buffer configuration")
        for step in self.config['steps']:
            if step['name'] == "connector":
                self.connector = Connector.Connector(step['config'], self.buffer)
        self.edgeOrchestrator = EdgeOrchestrator.EdgeOrchestrator(self.config, self.buffer)
        for mode_key in ['buffer', 'steps']:
            if mode_key not in self.config.keys():
                self.errors.append(' %s missing in Mode config' % mode_key)
                self.logger.error(' %s missing in Mode config' % mode_key)
        ############

        #self.load_config()
        # ERROR-CHECKER-THREAD
        self.error_checker_thread = threading.Thread(target=self.error_checker, name="Error Checker")
        self.error_checker_thread.start()
        # GET-INPUT-THREAD
        self.get_input_thread = threading.Thread(target=self.get_input, name="Get Input")
        self.get_input_thread.start()

    def error_checker(self):
        error = False
        info = False
        self.info_checker()
        self.load_menu()
        try:
            while self.menuchoice != "exit":
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
                if len(self.edgeOrchestrator.errors) != 0:
                    self.errors += self.edgeOrchestrator.errors
                    self.edgeOrchestrator.errors.clear()
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
        try:
            if self.connector.info is not None:
                self.info.append(self.connector.info)
                self.connector.info = None
            if len(self.edgeOrchestrator.info) != 0:
                self.info += self.edgeOrchestrator.info
                self.edgeOrchestrator.info.clear()
        except Exception as error:
            self.errors.append(str(self.__class__) + ": " + str(error))
            self.logger.exception("ERROR:")

    def get_input(self):
        while self.menuchoice != "exit":
            self.menuchoice = input()
            if self.menuchoice == '1':
                if self.edgeOrchestrator.status == "stop":
                    self.edgeOrchestrator.status = "start"
                else:
                    self.edgeOrchestrator.status = "stop"
            elif self.menuchoice == '2':
                if self.connector.status == "stop":
                    self.connector.status = "start"
                else:
                    self.connector.status = "stop"
            elif self.menuchoice == '3':
                self.info.append("Reading mode...")
                self.load_config()
            elif self.menuchoice == '4':
                self.menuchoice = "exit"
                if self.edgeOrchestrator is not None:
                    self.edgeOrchestrator.status = "stop"
                    self.edgeOrchestrator.terminated = True
                if self.connector is not None:
                    self.connector.status = "stop"
                    self.connector.terminated = True
                print("Goodbye")
                return
            with self.menu_lock:
                self.load_menu()

    def load_config(self):
        mode_path = r"./mainconfig/config.json"
        try:
            with open(mode_path) as json_file:
                self.config = json.load(json_file)
                json_file.close()
            if self.edgeOrchestrator is not None:
                self.edgeOrchestrator.status = "stop"
                self.edgeOrchestrator.terminated = True
            if self.connector is not None:
                self.connector.status = "stop"
                self.connector.terminated = True
            time.sleep(3)
            if 'buffer' in self.config and 'config' in self.config['buffer']:
                self.buffer = Buffer.Buffer(self.config['buffer']['config'])
            else:
                self.errors.append("Error in Buffer configuration")
            for step in self.config['steps']:
                if step['name'] == "connector":
                    self.connector = Connector.Connector(step['config'], self.buffer)
            self.edgeOrchestrator = EdgeOrchestrator.EdgeOrchestrator(self.config, self.buffer)
            for mode_key in ['buffer', 'steps']:
                if mode_key not in self.config.keys():
                    self.errors.append(' %s missing in Mode config' % mode_key)
                    self.logger.error(' %s missing in Mode config' % mode_key)

        except Exception as error:
            self.errors.append(str(self.__class__) + ": " + str(error))
            self.logger.exception("ERROR:")

    def load_menu(self):
        print("\nWelcome to OIH Edge Interface\n")
        # Error output
        if len(self.errors) != 0 or len(self.info) != 0:
            print("##############################")
            for error in self.errors:
                print(f"{self.red}Error: {self.endc}" + str(error))
            for info in self.info:
                print(f"{self.green}Info: {self.endc}" + str(info))
            print("##############################\n")
            self.info.clear()
            self.errors.clear()
        # EdgeOrchestrator status
        print(f"EdgeOrchestrator: " +
              (f"{self.red}Stopped{self.endc}" if (self.edgeOrchestrator.status == 'stop') else
               f"{self.green}Started{self.endc}"))
        # Connector status
        print(f"Connector: " +
              (f"{self.red}Stopped{self.endc}" if (self.connector.status == 'stop') else
               f"{self.green}Started{self.endc}"))
        # print menu
        print("\nWaiting for command:\n")
        print("1) Start EdgeOrchestrator" if (self.edgeOrchestrator.status == 'stop') else "1) Stop EdgeOrchestrator")
        print("2) Start Connector" if (self.connector.status == 'stop') else "2) Stop Connector")
        print("3) Reload mode")
        print("4) Exit\n")
        # wait for user input


if __name__ == '__main__':
    main = Main()
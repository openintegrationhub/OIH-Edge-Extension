from abc import ABC, abstractmethod
import logging
import threading
from component.Buffer import Buffer


class ConnectorBaseClass(ABC, threading.Thread):
    @abstractmethod
    # Connector is created by Main-Class and given a config and buffer object
    def __init__(self, config: dict, buffer: Buffer):
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
        """ The run() method can be used to query a data source. Write errors to self.error field. If self.error is not
        emptry Main-Class will set self.status to "stop". """
        # do something when Connector is started for the first time
        while not self.terminated:
            # do something while Connector has stopped but is still running
            while self.status == "start":
                # do something while Connector is running and self.status is "start" i.e. query data source
                pass
        # do something when Connector has been terminated
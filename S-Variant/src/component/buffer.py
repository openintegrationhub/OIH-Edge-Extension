# -*- coding: utf-8 -*-
"""
Buffer Component of the OIH Edge
"""

from typing import Union
from threading import Lock

from component.component_base_class import ComponentBaseClass


class Buffer(ComponentBaseClass):
    """
    This class is used to buffer the incoming data of the connectors and of the
    analysis components.

    Args:
    -----
        config (dict): Given configuration.

    Attributes:
    -----------
        max_size (int): Maximum size of the buffer.

        max_policy (str): Policy to handle max_size.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        buffer_empty (bool): Signalizes, that the buffer is empty.

        buffer_ready (bool): This field keeps the lock actives as long, as the
        writing process is not finished.

        buffer_lock (threading.Lock): This field assures that the buffer
        cannot be written at the same time, by different instances.

        buffer (dict): Buffered data.

        database (dict): TO-DO

        type_choice (int): Either local buffering (0) or remote buffering (1).

    Methods:
    --------
        fill_buffer(data: dict): This method passes the incoming data to the
        specified buffer. Either to the local buffer or the remote buffer.

        process(data: dict): This method passes the buffered data to the
        edge_orchestrator.

        local_buffer(data: dict): With this method the given data will be
        stored in memory.

        remote_buffer(data: dict): TO-DO: Implement.
    """
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration.
        """
        super().__init__(config)
        self.max_size = config['maxsize']
        self.max_policy = config['maxpolicy']
        self.error = None
        self.info = None
        self.buffer_empty = True
        self.buffer_ready = False
        self.buffer_lock = Lock()
        self.buffer = {
            'metadata': {
                'deviceID': ""
            },
            'data': {
            }
        }
        if 'database' in config:
            self.database = config['database']
        if config['type'] == 'local':
            self.type_choice = 0
        elif config['type'] == 'remote':
            self.type_choice = 1
        self.procedure_call = [self.local_buffer, self.remote_buffer]

    def fill_buffer(self, data: dict):
        """This method passes the incoming data to the specified buffer method.
        Either to the local buffer or the remote buffer.
        """
        self.procedure_call[self.type_choice](data)

    def process(self, data: dict) -> Union[dict, None]:
        """This method passes the data of the buffer to the
        edge_orchestrator.

        Parameters:
        -----------
            data (dict): TO-IGNORE.

        Returns:
            Either None or the buffered data.
        """
        try:
            if not self.buffer_ready:
                return None
            else:
                with self.buffer_lock:
                    self.buffer_empty = True
                    self.buffer_ready = False
                    return self.buffer
        except (ValueError, Exception) as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR")

    def local_buffer(self, data: dict):
        """With this method the given data will be stored in memory.

        Parameters:
        -----------
            data (dict): Data to be buffered.
        """
        with self.buffer_lock:
            if self.buffer_empty:
                self.buffer_empty = False
                self.buffer['metadata'] = data['metadata']
                self.buffer['data'] = {}
                for sensor in data['data']:
                    self.buffer['data'][sensor] = []
                    for value_set in data['data'][sensor]:
                        self.buffer['data'][sensor].append(value_set)
            else:
                for device in data['metadata']:
                    if device not in self.buffer['metadata'].keys():
                        self.buffer['metadata'][device] \
                            = data['metadata'][device]
                for sensor in data['data']:
                    if sensor not in self.buffer['data'].keys():
                        self.buffer['data'][sensor] = []
                    for value_set in data['data'][sensor]:
                        self.buffer['data'][sensor].append(value_set)
            self.buffer_ready = True

    def remote_buffer(self, data: dict):
        """TO-DO: Implement."""
        pass

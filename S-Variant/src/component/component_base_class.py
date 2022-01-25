# -*- coding: utf-8 -*-
"""
component_base_class Component of the OIH-Edge.
"""

from abc import ABC, abstractmethod
import logging


class ComponentBaseClass(ABC):
    """This class is used as super class of all components.

    Attributes:
    -----------
        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

    Methods:
    --------
        process(data: dict): Method is called by orchestrator and is given a
        dict with data. Return same or processed data on success, None on fail.
    """
    @abstractmethod
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info arrays to save
        messages.
        """
        self.config = config
        self.error = None
        self.info = None
        self.logger = logging.getLogger()

    @abstractmethod
    def process(self, data: dict) -> dict:
        """Method is called by orchestrator and is given a dict with data.
        Return same or processed data on success, None on fail.
        """
        pass

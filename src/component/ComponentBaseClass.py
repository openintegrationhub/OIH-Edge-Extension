from abc import ABC, abstractmethod
import logging


class ComponentBaseClass(ABC):
    @abstractmethod
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info arrays to save messages."""
        self.config = config
        self.error = None
        self.info = None
        self.logger = logging.getLogger()

    @abstractmethod
    def process(self, data: dict) -> dict:
        """Method is called by orchestrator and is given a dict with data. Return same or
        processed data on success, None on fail."""
        pass

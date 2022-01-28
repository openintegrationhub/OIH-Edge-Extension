# -*- coding: utf-8 -*-
"""
WebhookConnector Component of the On-Edge Adapter.
"""
from typing import Union

import requests
from pandas.io import json

from component.component_base_class import ComponentBaseClass


class WebhookConnector(ComponentBaseClass):
    """This class is used to connect to a webhook.

    Attributes:
    -----------
        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        url (str): In the config specified url to connect to.

    Methods:
    --------
        process(data: dict):
    """
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration.

            buffer (Buffer): Buffer instance in which the data of the
            connector will be stored.
        """
        super().__init__(config)
        self.config = config
        self.error = None
        self.info = None
        self.url = self.config["url"]

    def process(self, data: dict) -> Union[dict, None]:
        """
        TO-DO: Docstring
        """
        oih_data = {'data': json.dumps(data['data']),
                   'metadata': json.dumps(data['metadata'])}
        try:
            response = requests.post(url=self.url,
                                     json=oih_data)
            self.logger.info(response)
            self.logger.error("TEST")
            return data
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
            return None

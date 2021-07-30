import requests
from pandas.io import json

from component.ComponentBaseClass import ComponentBaseClass


class WebhookConnector(ComponentBaseClass):
    def __init__(self, config: dict):
        super().__init__(config)
        self.config = config
        self.error = None
        self.info = None
        self.url = self.config["url"]

    def process(self, data: dict) -> dict:
        oihdata = {'data': json.dumps(data['data']), 'metadata': json.dumps(data['metadata'])}
        try:
            response = requests.post(url=self.url, json=oihdata)
            self.logger.info(response)
            self.logger.error("TEST")
            return data
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")
# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 14:14:44 2022
Anonymizer Faust Stream of OIH-Edge Extension

@author: AUS
"""

import copy
import json
from typing import Union
import faust
import numpy as np
import pandas as pd
import log



class Anonymizer:
    """
    This class is used to anonymize a given data stream
    """

    def __init__(self, config: dict):
        self.config = config
        self.sensor_config = None
        self.ano_methods = ['thresholder', 'skip_n', 'hider', 'randomizer',
                            'categorizer']
        self._source_topic = self.config['source_topic']
        self._ann_topic = self.config['ann_topic']
        self.config = self.config['sensor_config']
        self.iter_data = {}
        self.ret_data = {}
        self.error = None
        self.info = None
        self.wait = True

    @staticmethod
    def create_app(config: dict):
        """Create and configure a Faust based kafka-aggregator application.
        Parameters
        ----------
        config : `Configuration`, optional
            The configuration to use.  If not provided, the default
            :ref:`Configuration` will be used.
        """

        log.logging.info("Kafka Broker is", config['broker'])
        app = faust.App(
            id=config['id'],
            broker=config['broker'])
        return app

    def synchron(self, data: list, sensor: str):
        """
        This function is used when the sensor method is None.
        The data will not be cached, but forwarded synchronously without any
        anonymization.
        Parameters
        ----------
        data : list
            the list consists of dictionaries with a timestamp and a value
            e.g.
            {'timestamp': '2020-06-20T16:12:54', 'value': '34534,345'}.
        sensor : string
            Name of the sensor.

        Returns
        -------
        None.
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def hider(self, data: list, sensor: str):
        """
        This function is used to hide certain fields.
        """
        self.iter_data['data'][sensor] = []

    def thresholder(self, data: list, sensor: str):
        """
        This function replaces every value which is outside a certain threshold
        with a substitute depending of the value being smaller than the left
        hand side of the threshold or being bigger than the right hand side of
        the threshold.
        """
        try:
            if len(data) >= self.sensor_config['window']:

                (low_ts, up_ts) = self.sensor_config['threshold']
                (low_sub, up_sub) = self.sensor_config['substitution']
                self.wait = False
                modulo = self._calc_modulo(len(data),
                                           self.sensor_config['window'])

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    ann_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]

                else:
                    ann_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                ann_data = np.array_split(ann_data, len(ann_data)
                                          / self.sensor_config['window'])

                for ann in ann_data:
                    ann['value'][ann['value'] > up_ts] = up_sub
                    ann['value'][(ann['value'] < low_ts)
                                 & (ann['value'] != up_sub)] = low_sub

                    self.ret_data['data'][sensor].extend(
                        ann.to_dict(orient='records')[:])
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

    def skip_n(self, data: list, sensor: str):
        """
        This function only shows every n-th element.
        """
        try:
            if len(data) >= self.sensor_config['N']:
                self.wait = False
                modulo = self._calc_modulo(len(data), self.sensor_config['N'])

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    ann_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]

                else:
                    ann_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                ann_data = np.array_split(ann_data, len(ann_data)
                                          / self.sensor_config['N'])

                self.ret_data['data'][sensor] = [
                    {'timestamp': pd.DataFrame(ann)['timestamp'].iloc[-1],
                     'value': pd.DataFrame(ann)['value'].iloc[-1]}
                    for ann in ann_data]
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

    def randomizer(self, data: list, sensor: str):
        """
        This function adds a random value onto the given data.
        """
        try:
            if len(data) >= self.sensor_config['window']:

                self.wait = False
                modulo = self._calc_modulo(len(data),
                                           self.sensor_config['window'])

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    ann_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]
                else:
                    ann_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                ann_data = np.array_split(ann_data, len(ann_data)
                                          / self.sensor_config['window'])

                if self.sensor_config['distribution']['name'] == 'random':
                    range_left, range_right \
                        = self.sensor_config['distribution']['range']
                    for ann in ann_data:
                        ann['value'] = ann['value'] + np.random.randint(
                            range_left, range_right, ann.shape[0])
                        self.ret_data['data'][sensor].extend(
                            ann.to_dict(orient='records')[:])

        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

    def categorizer(self, data: list, sensor: str):
        """
        This function categorizes the given Data into certain labels.
        e.g.
        'cats': [10,20,30]
        'lables' [1,2]
        Every value < 20 gets categorized into the field 1 and every
        value > 20 get categorized into the field 2
        """
        try:
            self.wait = False
            self.iter_data['data'][sensor] = []

            df_data = pd.DataFrame(data)

            if isinstance(self.sensor_config['cats'], list):
                df_data['value'] = pd.cut(df_data['value'],
                                          self.sensor_config['cats'],
                                          labels=self.sensor_config['labels'])
            elif isinstance(self.sensor_config['cats'], tuple):
                low, high, num = self.sensor_config['cats']
                lab = list(np.linspace(low, high, num))
                lab.insert(0, -float("inf"))
                lab.insert(len(lab), float("inf"))
                df_data['value'] = pd.cut(df_data['value'], lab,
                                          labels=False)
                del lab

            self.ret_data['data'][sensor].extend(df_data.to_dict(
                orient='records')[:])
            del df_data
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

    def _calc_modulo(self, data_size: int, window_size: int):
        """
        Doc TO-DO

        Parameters
        ----------
        data_size : int
            DESCRIPTION.
        window_size : int
            DESCRIPTION.

        Returns
        -------
        mod : TYPE
            DESCRIPTION.

        """
        mod = data_size % window_size
        return mod

    def _clean_ret_data(self):
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _call_anom_method(self, sensor: str):
        if self.sensor_config['name'] is None:
            self.synchron(self.iter_data['data'][sensor], sensor)
        elif self.sensor_config['name'] == 'hider':
            self.hider(self.iter_data['data'][sensor], sensor)
        elif self.sensor_config['name'] == 'categorizer':
            self.categorizer(self.iter_data['data'][sensor], sensor)
        elif self.sensor_config['name'] == 'thresholder':
            self.thresholder(self.iter_data['data'][sensor], sensor)
        elif self.sensor_config['name'] == 'skip_n':
            self.skip_n(self.iter_data['data'][sensor], sensor)
        elif self.sensor_config['name'] == 'randomizer':
            self.randomizer(self.iter_data['data'][sensor], sensor)

    def _process(self, data: dict) -> Union[dict, None]:
        """
        Doc TO-DO

        Parameters
        ----------
        data : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        try:
            if len(self.ret_data) == 0:
                self.ret_data = copy.deepcopy(data)
                self._clean_ret_data()
            else:
                self._clean_ret_data()

            # If iter_data is not empty, than extend the sensor values with the
            # incoming data.
            if len(self.iter_data) == 0:
                self.iter_data = copy.deepcopy(data)
            else:
                for sensor in self.iter_data['data']:
                    self.iter_data['data'][sensor].extend(data['data'][sensor])

            for sensor in self.iter_data['data']:
                if sensor in self.config:
                    self.sensor_config = self.config[sensor]
                else:
                    self.sensor_config = self.config['default']

                if self.sensor_config['name'] not in self.ano_methods:
                    raise ValueError(f"Anoynmization method "
                                     f"{self.sensor_config['name']} is not "
                                     f"known")

                self._call_anom_method(sensor)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            print("Error:", self.error)

        if not self.wait:
            self.wait = True
            return self.ret_data
        return None

    def process(self, app: faust.App):
        """
        :param app: Faust app.
        """
        source_topic = app.topic(self._source_topic)
        ann_topic = app.topic(self._ann_topic)
        log.logging.info("Source Topic", source_topic)

        @app.agent(source_topic)
        async def stream_anonymize(stream):
            """Process incoming events from the source topics."""
            async for event in stream:
                res = self._process(event)
                if res:
                    await ann_topic.send(value=res)


if __name__ == '__main__':
    MODE_PATH = r"./configs/config.json"
    with open(MODE_PATH) as json_file:
        config = json.load(json_file)
        json_file.close()
    Ann = Anonymizer(config)
    app = Ann.create_app(config['faust_config'])
    Ann.process(app)
    app.main()

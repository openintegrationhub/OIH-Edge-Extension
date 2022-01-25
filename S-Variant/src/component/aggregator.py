# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Component of the OIH-Edge.
"""

__author__ = "AUS"

import copy
from typing import Union

import numpy as np
import pandas as pd

from component.component_base_class import ComponentBaseClass


class Aggregator(ComponentBaseClass):
    """This class is used to aggregate an incoming data stream.

    Args:
    -----
        config (dict): Given configuration.

    Attributes:
    ----------
        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

        method (str): either aggregate or synchron.

        window (int): Quantity intervals at which this class aggregates the
        data.

        agg_methods (list[str]): Available aggregation methods.

        iter_data (dict): Buffer raw data.

        ret_data (dict): Aggregated output data.

        wait (bool): While this field is 'True' return 'None', otherwise return
        aggregated data.

    Methods:
    --------
        synchron(data: list, sensor: str): This method is used when the sensor
        method is None. The data will not be cached, but forwarded
        synchronously without any aggregation.

        aggregate(data: list, sensor: str): This method is used to aggregate
        the given data. The data will be aggregated as specified in the config,
        for the given sensor.

        _clean_ret_data(): This method clears the output data.

        _calc_modulo(data_size: int, window_size: int): This function
        determines the mod of the data_size and the window_size.

        _process(data: dict): This method initializes the the iter_data and
        ret_data field and appends new incoming data. Furthermore, it passes
        the buffered data to the specified method.

        process(data: dict): This method passes the given data to the _process
        method and returns its output.
    """
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration of the Aggregator component.
            e.g.:
                code-block:: json

                'config': {
                    'default': ('mean',5),
                    'Devices.ReactorTemp': ('last',5)
                    ...
                }

            instead of ('mean',5), you could also use ('None','None')
        """
        super().__init__(config)
        self.config = config
        self.method = self.config['default'][0]  # default aggregation method
        self.window = self.config['default'][1]  # default window_size
        self.agg_methods = ['mean', 'median', 'last']  # implemented
        # aggregation methods
        self.iter_data = {}  # buffer raw data
        self.ret_data = {}  # aggregated output data
        self.error = None
        self.info = None
        self.wait = True

    def synchron(self, data: list, sensor: str):
        """This method is used when the sensor method is None.

        The data will not be cached, but forwarded synchronously without any
        aggregation.

        Parameters:
        ----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value': '34534,
            345'}.

            sensor (str): Name of the sensor.

        Returns:
        -------
        None.
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def aggregate(self, data: list, sensor: str):
        """This method is used to aggregate the given data.
        The data will be aggregated as specified in the config, for the given
        sensor. There are three aggregation methods available, mean, median
        and last.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value': '34534,
            345'}.

            sensor (str): Name of the sensor.

        Raises:
        -------
            ValueError:
                Raises a ValueError if an unknown aggregation method is
                specified.

        Returns:
        --------
            None.
        """
        try:
            if len(data) >= self.window:
                self.wait = False
                modulo = self._calc_modulo(len(data), self.window)

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    agg_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]
                else:
                    agg_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                agg_data = np.array_split(agg_data, len(agg_data)
                                          / self.window)

                if self.method not in self.agg_methods:
                    raise ValueError(f"Aggregation method {self.method} not"
                                     f"known")

                if self.method == 'mean':
                    # agg_data= [np.mean(d) for d in agg_data]
                    self.ret_data['data'][sensor] = [{'timestamp':
                                                          pd.DataFrame(ad)
                                                          ['timestamp']
                                                              .iloc[-1],
                                                      'value':
                                                          pd.DataFrame(ad)
                                                          ['value']
                                                              .aggregate(
                                                              'mean')}
                                                     for ad in agg_data]
                elif self.method == 'median':
                    # agg_data= [np.median(d) for d in agg_data]
                    self.ret_data['data'][sensor] = [{'timestamp':
                                                          pd.DataFrame(ad)
                                                          ['timestamp']
                                                              .iloc[-1],
                                                      'value':
                                                          pd.DataFrame(ad)
                                                          ['value']
                                                              .aggregate(
                                                              'median')}
                                                     for ad in agg_data]
                elif self.method == 'last':
                    # agg_data= [d[-1] for d in agg_data]
                    self.ret_data['data'][sensor] = [{'timestamp':
                                                          pd.DataFrame(ad)
                                                          ['timestamp']
                                                              .iloc[-1],
                                                      'value':
                                                          pd.DataFrame(ad)
                                                          ['value']
                                                              .iloc[-1]}
                                                     for ad in agg_data]
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")

    def _clean_ret_data(self):
        """This method clears the output data."""
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    @staticmethod
    def _calc_modulo(data_size: int, window_size: int) -> int:
        """This function determines the mod of the data_size and the
        window_size.

        Parameters:
        -----------
            data_size (int): size of the given data.

            window_size (int): given window size.

        Returns:
        --------
            mod (int):
                mod value of data_size and window_size.
        """
        mod = data_size % window_size
        return mod

    def _process(self, data: dict) -> Union[dict, None]:
        """This method initializes the iter_data and ret_data field and
        appends new incoming data. Furthermore, it passes the buffered data
        to the specified method.

        Parameters:
        -----------
            data (dict): incoming data stream.

            code-block:: json

            {
                'data': {
                    'sensor1': [
                        {'timestamp':'2020-06-20T16:12:54',
                        'value':'34534,345'},
                        {'timestamp':'2020-06-20T16:12:55',
                        'value':'34534,345'}],
                    'sensor2': [
                        {'timestamp':'2020-06-20T16:12:54',
                        'value':'closed'},
                        {'timestamp':'2020-06-20T16:12:55',
                        'value':'closed'}],
                    ...
                    ...
                    ...
                }
            }

        Returns:
        --------
            ret_data (dict): Same structure as the input.
            Just with the aggregated data (if not in synchron mode).
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
                    self.iter_data['data'][sensor].extend(
                        data['data'][sensor])

            for sensor in self.iter_data['data']:
                if sensor in self.config:
                    self.method = self.config[sensor][0]
                    self.window = self.config[sensor][1]
                else:
                    self.method = self.config['default'][0]
                    self.window = self.config['default'][1]

                if self.method is None:
                    self.synchron(self.iter_data['data'][sensor], sensor)
                else:
                    self.aggregate(self.iter_data['data'][sensor], sensor)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR:")

        if not self.wait:
            self.wait = True
            return self.ret_data
        else:
            # self.info = "Aggregator didn\'t achieve necessary window size"
            return None

    def process(self, data: dict) -> Union[dict, None]:
        """This method passes the given data to the _process method and
        returns its output.

        Parameters:
        -----------
            data (dict): incoming data stream

            code-block:: json

            {
                'data':{
                    'sensor1':[
                            {'timestamp':'2020-06-20T16:12:54',
                            'value':'34534,345'},
                            {'timestamp':'2020-06-20T16:12:55',
                            'value':'34534,345'}],
                    'sensor2':[
                            {'timestamp':'2020-06-20T16:12:54',
                            'value':'closed'},
                            {'timestamp':'2020-06-20T16:12:55',
                            'value':'closed'}],
                    ...
                    ...
                    ...
                }
            }

        Returns:
        --------
            dict
            Same structure as the input.
            Just with the aggregated data (if not in synchron mode).
        """
        return self._process(data)

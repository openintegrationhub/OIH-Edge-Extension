# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Component of the On-Edge Adapter.
"""

__author__ = "AUS"

import copy
from datetime import datetime
from typing import Union

import pandas as pd

from component.component_base_class import ComponentBaseClass


class Aggregator(ComponentBaseClass):
    """This class is used to aggregate an incoming data stream.

    Args:
    -----
        config (dict): Given configuration.

    Attributes:
    -----------
        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

        method (string): Either aggregate or synchron.

        window (int): Time intervals at which this class aggregates the data.

        iter_data (dict): Buffer raw data.

        ret_data (dict): Aggregated output data.

        wait (bool): While this field is 'True' return 'None', otherwise return
        aggregated data.

        reference_ts_old (dict): This field stores the timestamps, at which
        the aggregation takes place.

        reference_ts_new (dict): This field stores the timestamps, at which
        the new aggregation takes place.

        reference_ts_old_setted (bool): True if ts_old is setted.

    Methods:
    --------
        synchron(data: list, sensor: str): This method is used when the sensor
        method is None. The data will not be cached, but forwarded
        synchronously without any aggregation.

        _calc_ref_ts(last_ts: datetime, cur_ts: datetime): This method is used
        to determine the next timestamp for the next aggregation.

        aggregate(data: list, sensor: str): This is used to aggregate the given
        data. The data will be aggregated as specified in the config, for the
        given sensor.

        _clean_ret_data(): This method clear the output data.

        _clean_ts_ref_value(): This method clears the timestamp references.

        _calc_modulo(data_size: int, window_size: int): This function
        determines the mod of the data_size and the window_size.

        _process(data: dict): This method initializes the iter_data and
        ret_data fields and appends new incoming data. Furthermore,
        it passes the buffered data to the specified method.

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

                'config':{
                        'default': {"method":'mean',
                                    "window_size":'5s'},
                        'sensor2': {"method":'mean',
                                    "window_size":'5s'}
                        '...':{...}
                }
        """
        super().__init__(config)
        self.config = config
        self.method = self.config['default']['method']  # default aggregation
                                                        # method
        self.window = self.config['default']['window_size']  # default
                                                            # window_size
        # self.agg_methods=['mean','median','last','first','sum','min','max']
        # #implemented aggregation methods
        self.iter_data = {}  # buffer raw data
        self.ret_data = {}  # aggregated output data
        self.error = None
        self.info = None
        self.wait = True
        self.reference_ts_old = {}
        self.reference_ts_new = {}  # To-Do: combine to one reference-info
        self.reference_ts_old_setted = False

    def synchron(self, data: list, sensor: str):
        """
        This method is used when the sensor method is None.

        The data will not be cached, but forwarded synchronously without any
        aggregation.

        Parameters
        ----------
            data (list): the list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value': '34534,
            345'}.

            sensor (str): Name of the sensor.

        Returns
        -------
            None.
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def _calc_ref_ts(self, last_ts: datetime, cur_ts: datetime) -> datetime:
        """
        This method is used to determine the next timestamp for the next
        aggregation.

        Parameters:
        -----------
            last_ts (timestamp):
            cur_ts (timestamp):

        Returns:
        --------
            datetime
        """
        mod = (last_ts.timestamp() - cur_ts.timestamp()) \
              % (float(self.window.split('s')[0]))
        new_ts = last_ts.timestamp() - mod + float(self.window.split('s')[0])

        return datetime.fromtimestamp(new_ts)

    def aggregate(self, data: list, sensor: str):
        """
        This method is used to aggregate the given data.
        The data will be aggregated as specified in the config, for the given
        sensor.

        There are three aggregation methods available, mean, median and last.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp
            and a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
        """
        if len(data) > 1:
            if datetime.strptime(data[-1]['timestamp'],
                                 "%Y-%m-%dT%H:%M:%S.%f") \
                    > self.reference_ts_new['data'][sensor]:
                self.wait = False
                self.reference_ts_old['data'][sensor] = self.reference_ts_new[
                    'data'][sensor]
                self.reference_ts_new['data'][sensor] = self._calc_ref_ts(
                    datetime.strptime(data[-1]['timestamp'],
                                      "%Y-%m-%dT%H:%M:%S.%f"),
                    self.reference_ts_old['data'][sensor])

                data_df = pd.DataFrame(data)
                data_df['timestamp'] = pd.to_datetime(
                    data_df['timestamp'],
                    format="%Y-%m-%dT%H:%M:%S.%f")

                agg_data = data_df[data_df['timestamp']
                                   <= self.reference_ts_old['data'][sensor]]

                non_agg_size = len(data_df) - len(agg_data)

                agg_data.index = agg_data['timestamp']

                if non_agg_size == 0:
                    self.iter_data['data'][sensor] = []
                else:
                    self.iter_data['data'][sensor] = data[-non_agg_size:]

                agg_data = agg_data.groupby(
                    pd.Grouper(freq=self.window,
                               origin=pd.Timestamp(
                                   self.reference_ts_old['data'][sensor])))\
                    .aggregate(self.method)
                agg_data['timestamp'] = agg_data.index
                agg_data['timestamp'].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

                self.ret_data['data'][sensor] = agg_data.to_dict('records')

    def _clean_ret_data(self):
        """
        This method clears the output data.

        Returns:
        --------
            None.
        """
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _clean_ts_ref_values(self):
        """
        This method clears the timestamp references.

        Returns:
        --------
            None.
        """
        for sensor in self.reference_ts_old['data']:
            self.reference_ts_old['data'][sensor] = None
            self.reference_ts_new['data'][sensor] = None

    @staticmethod
    def _calc_modulo(data_size: int, window_size: int) -> int:
        """
        This function determines the mod of the data_size and the window_size.

        Parameters
        ----------
            data_size (int): size of the given data.

            window_size (int): given window size.

        Returns
        -------
            mod (int): mod value of data_size and window_size.
        """
        mod = data_size % window_size
        return mod

    def _process(self, data: dict) -> Union[dict, None]:
        """
        This method initializes the iter_data and ret_data fields and
        appends new incoming data. Furthermore, it passes the buffered data
        to the specified method.

        Parameters:
        -----------
            data (dict): incoming data stream.

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
            ret_data (dict): Same structure as the input.
            Just with the aggregated data (if not in synchron mode).
        """
        try:
            if len(self.ret_data) == 0:
                self.ret_data = copy.deepcopy(data)
                self._clean_ret_data()
            else:
                self._clean_ret_data()

            # If iter_data is not empty, than extend the sensor values with
            # the incoming data.
            if len(self.iter_data) == 0:
                self.iter_data = copy.deepcopy(data)
            else:
                for sensor in self.iter_data['data']:
                    self.iter_data['data'][sensor].extend(data['data'][sensor])

            if len(self.reference_ts_old) == 0:
                self.reference_ts_old = copy.deepcopy(data)
                self.reference_ts_new = copy.deepcopy(data)
                self._clean_ts_ref_values()

            for sensor in self.iter_data['data']:
                if sensor in self.config:
                    self.method = self.config[sensor]['method']
                    self.window = self.config[sensor]['window_size']
                else:
                    self.method = self.config['default']['method']
                    self.window = self.config['default']['window_size']

                if not self.reference_ts_old_setted and \
                        self.reference_ts_old['data'][sensor] is None:
                    first_ts = self.iter_data['data'][sensor][0]['timestamp']
                    ref_ts = datetime.fromtimestamp(
                        datetime.strptime(first_ts, "%Y-%m-%dT%H:%M:%S.%f")
                        .timestamp() + float(self.window.split('s')[0]))
                    self.reference_ts_new['data'][sensor] = ref_ts

                if self.method is None:
                    self.synchron(self.iter_data['data'][sensor], sensor)
                else:
                    self.aggregate(self.iter_data['data'][sensor], sensor)

            if None not in self.reference_ts_old['data'].values():
                self.reference_ts_old_setted = True

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
        """
        This method passes the given data to the _process method and
        returns its output.

        Parameters
        ----------
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

        Returns
        -------
            dict
            Same structure as the input.
            Just with the aggregated data (if not in synchron mode).
        """
        return self._process(data)

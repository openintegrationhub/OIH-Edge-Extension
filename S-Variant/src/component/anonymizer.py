# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 14:14:35 2020
Anonymizer Component of the OIH-Edge .
"""

__author__ = "AUS"

from typing import Union
import copy

import numpy as np
import pandas as pd

from component.component_base_class import ComponentBaseClass


# Input data format
# json_body={
#     'deviceID':'4711383',
#     'data':{
#         'sensor1':[
#                {'timestamp':'2020-06-20T16:12:54', 'value':'34534,345'},
#                {'timestamp':'2020-06-20T16:12:55', 'value':'34534,345'}
#               ],
#         'sensor2':[
#                {'timestamp':'2020-06-20T16:12:54', 'value':'closed'},
#                {'timestamp':'2020-06-20T16:12:55', 'value':'closed'}
#               ]
#         }
# }
#
#
# config={
#     'default': {
#         'name':'thresholder',
#             'window': 10,
#             'threshold':[100,200],
#             'substitution': [120,180]  #also calcuation or deletion
#             of th sub values is possible. e.g. ('delete','mean')
#         },
#     'Sensor2':{
#         'name':'skip_n',
#             'N': 10,
#         },
#     'Sensor3':{
#         'name':'featex',
#             'window': 10,
#             'feature': ['mean','std','var','kurtosis']
#         },
#     'Sensor4':{
#         'name':'randomizer',
#             'window': 10,
#             #'percent': 0.5,
#             'distribution': {'name': 'win_dist',
#                              'std': 1
#                               },
#                             {'name': 'random',
#                             'range': (1,100)
#                               }
#         },
#     'Sensor5':{
#         'name':'hider',
#         },
#     'Sensor6':{
#         'name':'categorizer',
#         'cats':[0,10,20,30,40,50],   #categories <10, 10-20, 20-30, 30-40,
#               >40   #-float("inf")
#         'labels':[1,2,3,4,5]    #len(labels) must be len(cats)-1
#         },
#     }
#
#


class Anonymizer(ComponentBaseClass):
    """This class is used to anonymize an incoming data stream.

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

        sensor_config (dict): Anonymization method of a sensor.

        ano_methods (list): List of available anonymization methods.

        iter_data (dict): Buffer raw data.

        ret_data (dict): Anonymized output data.

        wait (bool): While this field is 'True' return 'None', otherwise return
        anonymized data.

    Methods:
    --------
        synchron(data: list, sensor: str): This method is used when the sensor
        method is None. The data will not be cached, but forwarded
        synchronously without any anonymization.

        hider(data: list, sensor: str): This method is used to 'hide' the given
        field.

        thresholder(data: list, sensor: str): This method replaces every value
        which is outside a certain threshold with a substitute depending on
        the value being smaller than the left hand side of the threshold or
        being bigger than the right hand side of the threshold.

        skip_n(data: list, sensor: str): This method only shows every n-th
        element of the given field.

        randomizer(data: list, sensor: str): This method adds a random value
        onto the given data. The random value is specified to be within a
        certain threshold.

        categorizer(self, data: list, sensor: str): This method categorizes the
        given Data into certain labels. e.g.
        'cats': [10,20,30]
        'lables' [1,2]
        Every value < 20 gets categorized into the field 1 and every
        value > 20 get categorized into the field 2

        correlation(data: list, sensor: str): TO-DO: Implement.

        process(data: dict): This method passes the given data to the _process
        method and returns its output.

        _calc_modulo(data_size: int, window_size: int): This function
        determines the mod of the data_size and the window_size.

        _clean_ret_data(): This method clears the output data.

        _process(data: dict): This method initializes the iter_data and
        ret_data fields and appends new incoming data. Furthermore,
        it passes the buffered data to the specified method.
    """
    def __init__(self, config: dict):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
            config (dict): User configuration of the Anonymizer component.
            e.g: as above.
        -----------
        """
        super().__init__(config)
        self.config = config
        self.sensor_config = None
        self.ano_methods = ['thresholder', 'skip_n', 'hider', 'randomizer',
                            'categorizer']
        self.iter_data = {}
        self.ret_data = {}
        self.error = None
        self.info = None
        self.wait = True

    def synchron(self, data: list, sensor: str):
        """
        This function is used when the sensor method is None.
        The data will not be cached, but forwarded synchronously without any
        anonymization.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def hider(self, data: list, sensor: str):
        """This method is used to 'hide' the given field.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
        """
        self.iter_data['data'][sensor] = []

    def thresholder(self, data: list, sensor: str):
        """This method replaces every value which is outside a certain
        threshold with a substitute depending on the value being smaller
        than the left hand side of the threshold or being bigger than the
        right hand side of the threshold.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
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
        """This method only shows every n-th element of the given field.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
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
        """This method adds a random value onto the given data. The random
        value is specified to be within a certain threshold.

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
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
                    range_left, range_right = self.sensor_config[
                        'distribution']['range']
                    for ann in ann_data:
                        ann['value'] = ann['value'] + np.random.randint(
                            range_left, range_right, ann.shape[0])
                        self.ret_data['data'][sensor].extend(
                            ann.to_dict(orient='records')[:])

                elif self.sensor_config['distribution']['name'] == 'win_dist':
                    # print('TO-DO')
                    return None
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

    def categorizer(self, data: list, sensor: str):
        """This method categorizes the given Data into certain labels.
        e.g.
        'cats': [10,20,30]
        'lables' [1,2]
        Every value < 20 gets categorized into the field 1 and every
        value > 20 get categorized into the field 2

        Parameters:
        -----------
            data (list): The list consists of dictionaries with a timestamp and
            a value e.g.: {'timestamp': '2020-06-20T16:12:54', 'value':
            '34534,345'}.

            sensor (str): Name of the sensor.

        Returns:
        --------
            None.
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

    def correlation(self, data: list, sensor: str):
        """TO-DO: Implement"""
        return data

    def process(self, data: dict) -> Union[dict, None]:
        """This method passes the given data to the _process method and
        returns its output.

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
            dict
            Same structure as the input.
            Just with the anonymized data (if not in synchron mode).
        """

        return self._process(data)

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
            mod (int): mod value of data_size and window_size.

        """
        mod = data_size % window_size
        return mod

    def _clean_ret_data(self):
        """This method clears the output data.

        Returns:
        --------
            None.
        """
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _process(self, data: dict) -> Union[dict, None]:
        """This method initializes the iter_data and ret_data fields and
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
                for sensor in data['data']:
                    if sensor not in self.ret_data['data']:
                        self.ret_data['data'][sensor] = []
                self._clean_ret_data()

            # If iter_data is not empty, than extend the sensor values with the
            # incoming data.
            if len(self.iter_data) == 0:
                self.iter_data = copy.deepcopy(data)
            else:
                for sensor in data['data']:
                    if sensor in self.iter_data['data']:
                        self.iter_data['data'][sensor].extend(
                            data['data'][sensor])
                    else:
                        self.iter_data['data'][sensor] = data['data'][sensor]

            for sensor in self.iter_data['data']:
                if sensor in self.config:
                    self.sensor_config = self.config[sensor]
                else:
                    self.sensor_config = self.config['default']

                if self.sensor_config['name'] not in self.ano_methods:
                    raise ValueError(f"Anoynmization method "
                                     f"{self.sensor_config['name']} is not "
                                     f"known")

                if self.sensor_config['name'] is None:
                    self.synchron(self.iter_data['data'][sensor], sensor)
                elif self.sensor_config['name'] == 'hider':
                    self.hider(self.iter_data['data'][sensor], sensor)
                elif self.sensor_config['name'] == 'categorizer':
                    self.categorizer(self.iter_data['data'][sensor], sensor)
                elif self.sensor_config['name'] == 'thresholder':
                    self.thresholder(self.iter_data['data'][sensor], sensor)
                elif self.sensor_config['name'] == 'skipN':
                    self.skipN(self.iter_data['data'][sensor], sensor)
                elif self.sensor_config['name'] == 'randomizer':
                    self.randomizer(self.iter_data['data'][sensor], sensor)

        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

        if not self.wait:
            self.wait = True
            return self.ret_data
        else:
            # self.info = ("Anonymizer didn\'t achieve necessary window size ")
            return None

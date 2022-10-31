# -*- coding: utf-8 -*-
"""
Created on Tue Jan  3 14:14:44 2022
Anonymizer Faust Stream of OIH-Edge Extension

@author: AUS
"""

import copy
import re
import signal
from typing import Union
from warnings import filterwarnings

import numpy as np
import pandas as pd
from component_base_class.component_base_class import ComponentBaseClass
from pandas.errors import SettingWithCopyWarning


class Anonymizer(ComponentBaseClass):
    """
    This class is used to anonymize a given data stream
    """

    def __init__(self):
        try:
            super().__init__()
        except Exception as error:
            print(f'Failure in Base Class, {error}')
            return
        filterwarnings('ignore', category=SettingWithCopyWarning)
        self.logger = self.get_logger()
        config_template = {
            "source_topic": "",
            "anom_topic": "",
            "faust_config": "",
            "sensor_config": ""
        }
        self.ano_methods = {
            'thresholder': self.thresholder,
            'skip_n': self.skip_n,
            'hider': self.hider,
            'randomizer': self.randomizer,
            'categorizer': self.categorizer
        }
        self.unprocessed_messages = 0
        self._source_topic = ''
        self._ann_topic = ''
        self.sensor_config = {}
        self.app_config = {}
        self.iter_data = {}
        self.ret_data = {}
        self.config = {}
        self.error = None
        self.info = None
        self.app = None
        self.wait = True
        self.load_config(config_template)
        if self.app and not self.terminated:
            self.app.main()

    def load_config(self, config_template: dict = None, source: str = 'file'):
        """ Loads the config for the component, either from env variables
        or from a file.

        :param config_template: dict with all required fields for the
        component to work.
        :param source: source of the config, either file or env
        :return: None
        """
        if source != 'file':
            conf = self.get_config(
                config_template,
                source=source,
                file_path=f'/config/{self.path_name}'
            )
        else:
            conf = self.wait_for_config_insertion()
        self.config = conf
        try:
            if self.config and all(keys in self.config
                                   for keys in config_template):
                self.app_config = self.config['faust_config']
                if self._source_topic != self.config['source_topic'] \
                        or self._ann_topic != self.config['anom_topic']:
                    self._source_topic = self.config['source_topic']
                    self._ann_topic = self.config['anom_topic']
                    self.app = self.create_app(self.app_config)
                    self.create_agent(self._source_topic,
                                      self._ann_topic,
                                      self.app,
                                      self._process)
            else:
                self.logger.error('Missing key(s) in config')
                print('Missing key(s) in config', flush=True)
                self.terminated = True
                return
        except ModuleNotFoundError as mod_err:
            self.logger.error(f'Invalid Kafka broker url: {mod_err}')
            print('Invalid kafka broker url', flush=True)
            self.terminated = True
        except Exception as error:
            self.logger.error(f'Error: {error} in load_config')
            self.terminated = True

    def synchron(self, data: list, sensor: str):
        """ Data will not be cached, but forwarded synchronously without any
        aggregation.

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def hider(self, data: list, sensor: str):
        """ Data will be cleared of the given sensor.

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        self.wait = False
        self.iter_data['data'][sensor] = []

    def thresholder(self, data: list, sensor: str):
        """ Replaces every value which is outside a certain threshold of the
        given data and substitutes depending on the value being smaller than
        the left hand side of the threshold or being bigger than the right
        hand side of the threshold.

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        try:
            if len(data) >= self.sensor_config['window']:

                (low_ts, up_ts) = self.sensor_config['threshold']
                (low_sub, up_sub) = self.sensor_config['substitution']
                self.wait = False
                modulo = self._calc_modulo(
                    len(data),
                    self.sensor_config['window']
                )

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    ann_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]

                else:
                    ann_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                ann_data['value'] = ann_data['value'].astype(dtype=float)
                ann_data = np.array_split(
                    ann_data.dropna(),
                    len(ann_data) / self.sensor_config['window']
                )

                for ann in ann_data:
                    ann['value'][ann['value'] > up_ts] = up_sub
                    ann['value'][(ann['value'] < low_ts)
                                 & (ann['value'] != up_sub)] = low_sub

                    self.ret_data['data'][sensor].extend(
                        ann.to_dict(orient='records')[:])
        except KeyError as key_err:
            self.logger.error('Invalid Configuration in thresholder')
            raise ValueError('Invalid Configuration') from key_err

    def skip_n(self, data: list, sensor: str):
        """ Skip every n-th element of the given data.

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        try:
            if len(data) >= self.sensor_config['N']:
                self.wait = False
                modulo = self._calc_modulo(
                    len(data),
                    self.sensor_config['N']
                )

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    ann_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]

                else:
                    ann_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                ann_data = np.array_split(
                    ann_data,
                    len(ann_data) / self.sensor_config['N']
                )

                self.ret_data['data'][sensor] = [
                    {'timestamp': pd.DataFrame(ann)['timestamp'].iloc[-1],
                     'value': pd.DataFrame(ann)['value'].iloc[-1]}
                    for ann in ann_data]
        except KeyError as key_err:
            self.logger.error('Invalid Configuration in skip_n')
            raise ValueError('Invalid Configuration') from key_err

    def randomizer(self, data: list, sensor: str):
        """ Add random values onto the given data.

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        try:
            if len(data) >= self.sensor_config['window']:

                self.wait = False
                modulo = self._calc_modulo(
                    len(data),
                    self.sensor_config['window']
                )

                if modulo != 0:
                    # This is the dataset which will be aggregated.
                    ann_data = pd.DataFrame(data[:-modulo])

                    # This is the remaining data in the buffer
                    self.iter_data['data'][sensor] = data[-modulo:]
                else:
                    ann_data = pd.DataFrame(data[:])
                    self.iter_data['data'][sensor] = []

                ann_data['value'] = ann_data['value'].astype(dtype=float)
                ann_data = np.array_split(
                    ann_data.dropna(),
                    len(ann_data) / self.sensor_config['window'])

                if self.sensor_config['distribution']['name'] == 'random':
                    range_left, range_right \
                        = self.sensor_config['distribution']['range']
                    for ann in ann_data:
                        ann['value'] = ann['value'] + np.random.randint(
                            range_left, range_right, ann.shape[0])
                        self.ret_data['data'][sensor].extend(
                            ann.to_dict(orient='records')[:])
        except KeyError as key_err:
            self.logger.error('Invalid configuration in randomizer')
            raise ValueError('Invalid Configuration') from key_err

    def categorizer(self, data: list, sensor: str):
        """ Categorizes the given Data into certain labels.
        e.g.
        'cats': [10,20,30]
        'lables' [1,2]
        Every value < 20 gets categorized into the field 1 and every
        value > 20 get categorized into the field 2

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        try:
            self.wait = False
            self.iter_data['data'][sensor] = []

            df_data = pd.DataFrame(data).dropna()
            df_data['value'] = df_data['value'].astype(dtype=float)

            df_data['value'][df_data['value'] <= self.sensor_config[
                'cats'][0]] = self.sensor_config['cats'][1]
            df_data['value'][df_data['value'] > self.sensor_config[
                'cats'][-1]] = self.sensor_config['cats'][-1]

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
        except KeyError as key_err:
            self.logger.error('Invalid configuration in categorizer')
            raise ValueError('Invalid Configuration') from key_err

    @staticmethod
    def _calc_modulo(data_size: int, window_size: int) -> int:
        """ Calculate the modulo of the given data.

        :param data_size: (int) stored data size
        :param window_size:
        :return: mod
        """
        mod = data_size % window_size
        return mod

    def _clean_ret_data(self):
        """ Clear the return data.

        :return: None
        """
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _process(self, data: dict) -> Union[dict, None]:
        """ Processes incoming data stream

        :param data: (dict) unprocessed data
        :return: (dict) processed data
        """
        try:
            if len(self.ret_data) == 0:
                self.ret_data = copy.deepcopy(data)
                self._clean_ret_data()
            else:
                self._clean_ret_data()

            # If iter_data is not empty, then extend the sensor values with the
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
                        self.ret_data['data'][sensor] = []

            for sensor in data['data']:
                if sensor in self.config['sensor_config']:
                    self.sensor_config = self.config['sensor_config'][sensor]
                else:
                    self.sensor_config = self.config['sensor_config'][
                        'default']

                if self.sensor_config['name'] not in self.ano_methods:
                    raise ValueError(f"Anoynmization method "
                                     f"{self.sensor_config['name']} is not "
                                     f"known")
                self.ano_methods[self.sensor_config['name']](
                    self.iter_data['data'][sensor],
                    sensor
                )
        except KeyError as key_err:
            self.unprocessed_messages += 1
            self.logger.warning(f'Invalid message format.'
                                f'Unprocessed messages: '
                                f'{self.unprocessed_messages}')
            self.logger.error(key_err)
        except ValueError as val_err:
            if re.match('Anonymization method .* is not known', str(val_err)):
                self.logger.error(f'Invalid anonymization method: {val_err}')
            elif str(val_err) != 'Invalid Configuration':
                self.logger.error(f'ValError: {val_err} in process')
            signal.raise_signal(signal.SIGTERM)
        except Exception as error:
            self.logger.error(f'Error: {error} in process')
            signal.raise_signal(signal.SIGTERM)

        if not self.wait:
            self.wait = True
            return self.ret_data


if __name__ == '__main__':
    ann = Anonymizer()

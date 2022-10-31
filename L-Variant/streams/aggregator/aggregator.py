# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Faust Stream of OIH-Edge Extension
"""

__author__ = 'AUS'

import copy
import signal
from datetime import datetime

import pandas as pd
from component_base_class.component_base_class import ComponentBaseClass


class Aggregator(ComponentBaseClass):

    def __init__(self):
        """
        Parameters
        ----------
        config : dict
        User configuration of the Aggregator component.
        e.g.:
        config= {
            'source_topic':'kafka_stream_component_agg_source',
            'aggregated_topic':'kafka_source_component_agg_sink',
            'faust_config':{
                id: "agg_test",
                broker: "kafka://localhost:19092",
                port: 6067
            },
            'sensor_config': {
                'default': {
                'method': 'mean',
                'window_size': '5s'
            },
            'sensor01': {
                'method': 'median',
                'window_size': '5s'
            }
        }
        """
        super().__init__()
        config_template = {
            "source_topic": "",
            "aggregated_topic": "",
            "faust_config": "",
            "sensor_config": ""
        }
        self.logger = self.get_logger()
        self.app_config = {}
        self.config = {}
        self.method = {}  # default aggregation method
        self.iter_data = {}  # buffer raw data
        self.ret_data = {}  # aggregated output data
        self.reference_ts_old = {}
        self.reference_ts_new = {}  # To-Do: combine to one reference-info
        self._source_topic = ''
        self._aggregated_topic = ''
        self.window = 0  # default window_size
        self.unprocessed_message = 0
        self.app = None
        self.error = None
        self.info = None
        self.wait = True
        self.reference_ts_old_setted = False
        self.load_config(config_template)
        if self.app and not self.terminated:
            self.app.main()

    def load_config(self, config_template=None, source='file'):
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
        try:
            if conf and all(key in conf for key in config_template.keys()):
                self.app_config = conf['faust_config']
                self.config = conf['sensor_config']
                self.method = self.config['default']['method']
                self.window = self.config['default']['window_size']
                if self._source_topic != conf['source_topic'] \
                        or self._aggregated_topic != conf['aggregated_topic']:
                    self._source_topic = conf['source_topic']
                    self._aggregated_topic = conf['aggregated_topic']
                    self.app = self.create_app(self.app_config)
                    self.create_agent(self._source_topic,
                                      self._aggregated_topic,
                                      self.app,
                                      self._process)
            else:
                self.logger.error('Missing key(s) in configuration')
                print('Missing key(s) in configuration', flush=True)
                self.terminated = True
                return
        except ModuleNotFoundError as mod_err:
            self.logger.error(f'Invalid Kafka broker url: {mod_err}')
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

    def _calc_ref_ts(self,
                     last_ts: datetime.timestamp,
                     cur_ts: datetime.timestamp):
        """
        This function is used to determine the next timestamp for the new
        window
        """
        mod = (last_ts.timestamp() - cur_ts.timestamp()) % (
            float(self.window.split('s')[0]))
        new_ts = last_ts.timestamp() - mod + float(self.window.split('s')[0])

        return datetime.fromtimestamp(new_ts)

    def aggregate(self,
                  data: list,
                  sensor: str):
        """ Aggregate the incoming data with the specified aggregation
        method

        :param data: (list) stored data which consists of dicts
        :param sensor: name of the sensor
        :return: None
        """
        if len(data) > 1:
            if datetime.strptime(data[-1]['timestamp'],
                                 "%Y-%m-%dT%H:%M:%S.%f") \
                    > self.reference_ts_new['data'][sensor]:
                self.wait = False
                self.reference_ts_old['data'][sensor] = \
                    self.reference_ts_new['data'][sensor]
                self.reference_ts_new['data'][sensor] = self._calc_ref_ts(
                    datetime.strptime(data[-1]['timestamp'],
                                      "%Y-%m-%dT%H:%M:%S.%f"),
                    self.reference_ts_old['data'][sensor])

                data_df = pd.DataFrame(data)
                data_df['timestamp'] = pd.to_datetime(
                    data_df['timestamp'],
                    format="%Y-%m-%dT%H:%M:%S.%f")

                agg_data = data_df[data_df['timestamp']
                                   < self.reference_ts_old['data'][sensor]]

                non_agg_size = len(data_df) - len(agg_data)

                agg_data.index = agg_data['timestamp']

                if non_agg_size == 0:
                    self.iter_data['data'][sensor] = []
                else:
                    self.iter_data['data'][sensor] = data[-non_agg_size:]

                agg_data = agg_data.groupby(
                    pd.Grouper(freq=self.window,
                               origin=pd.Timestamp(
                                   self.reference_ts_old['data'][sensor]))) \
                    .aggregate(self.method, numeric_only=True)
                agg_data['timestamp'] = agg_data.index
                agg_data['timestamp'].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

                self.ret_data['data'][sensor] = agg_data.to_dict('records')

    def _clean_ret_data(self):
        """ Clear all data of ret_data without deleting its structure.

        :return: None
        """
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _clean_ts_ref_values(self):
        """ Clear timestamp references, without deleting its structure

        :return: None
        """
        for sensor in self.reference_ts_old['data']:
            self.reference_ts_old['data'][sensor] = None
            self.reference_ts_new['data'][sensor] = None

    @staticmethod
    def _calc_modulo(data_size: int, window_size: int) -> int:
        """ Determine the modulo of the given data in regards
        to the window size

        :param data_size: (int) size of the stored data
        :param window_size: (int) user specified window size
        :return: (int)
        """
        mod = data_size % window_size
        return mod

    def _process(self, data: dict):
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

            # If iter_data is not empty, than extend the sensor values with
            # the incoming data.
            if len(self.iter_data) == 0:
                self.iter_data = copy.deepcopy(data)
            else:
                for sensor in data['data'].keys():
                    if sensor not in self.iter_data['data']:
                        try:
                            self.iter_data['data'][sensor] = data['data'][
                                sensor]
                            self.reference_ts_old['data'][sensor] = None

                            first_ts = self.iter_data['data'][sensor][0][
                                'timestamp']
                            ref_ts = datetime.fromtimestamp(
                                datetime.strptime(first_ts,
                                                  "%Y-%m-%dT%H:%M:%S.%f")
                                .timestamp() + float(
                                    self.window.split('s')[0]))

                            self.reference_ts_new['data'][sensor] = ref_ts
                        except ValueError:
                            self.logger.warning(f'Invalid timestring format.'
                                                f'Unprocessed Messages: '
                                                f'{self.unprocessed_message}')
                            self.unprocessed_message += 1
                            self.iter_data['data'][sensor] = []
                            continue
                    else:
                        self.iter_data['data'][sensor].extend(
                            data['data'][sensor])

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

                try:
                    if not self.reference_ts_old_setted \
                            and self.reference_ts_old['data'][sensor] is None:
                        first_ts = self.iter_data['data'][sensor][0][
                            'timestamp']
                        ref_ts = datetime.fromtimestamp(
                            datetime.strptime(first_ts, "%Y-%m-%dT%H:%M:%S.%f")
                            .timestamp() + float(self.window.split('s')[0]))
                        self.reference_ts_new['data'][sensor] = ref_ts
                except ValueError:
                    self.logger.warning(f'Invalid timestring format.'
                                        f'Unprocessed Messages: '
                                        f'{self.unprocessed_message}')
                    self.unprocessed_message += 1
                    continue
                if not self.method:
                    self.synchron(self.iter_data['data'][sensor], sensor)
                else:
                    self.aggregate(self.iter_data['data'][sensor], sensor)

            if None not in self.reference_ts_old['data'].values():
                self.reference_ts_old_setted = True

        except KeyError as key_err:
            self.logger.error(f'KeyError: {key_err}')
            signal.raise_signal(signal.SIGTERM)
        except Exception as error:
            self.logger.error(f'Error: {error}')
            signal.raise_signal(signal.SIGTERM)

        if not self.wait:
            self.wait = True
            return self.ret_data


if __name__ == '__main__':
    agg = Aggregator()

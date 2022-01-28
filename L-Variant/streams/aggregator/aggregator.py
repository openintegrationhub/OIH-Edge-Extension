# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 14:14:44 2020
Aggregator Faust Stream of OIH-Edge Extension

@author: AUS
"""
import copy
from datetime import datetime
import pandas as pd
import log
import json
import faust


class Aggregator:

    def __init__(self, config: dict):
        """
        Parameters
        ----------
        config : dict
        User configuration of the Aggregator component.
        e.g.:
        config= {
            'source_topic':'stream_agg_source',
            'aggregated_topic':'stream_agg_sink_1',
            'faust_config':{
                web_port:,
                id:,
                broker:)
            },
            'sensor_config': {
                'default': {"method": 'mean',
                        "window_size": '5s'},
                'sensor2': {"method": 'mean',
                        "window_size": '5s'}}
        }
        """

        self.config = config
        self.method = self.config['sensor_config']['default']['method']  #default aggregation method
        self.window = self.config['sensor_config']['default']['window_size'] #default window_size
        # Supports the 1 source topic -> 1 aggregated topic case for the moment
        self._source_topic = self.config['source_topic']
        self._aggregated_topic = self.config['aggregated_topic']
        self.config = self.config['sensor_config']
        self.iter_data = []  # buffer raw data
        self.ret_data = []  # aggregated output data
        self.error = None
        self.info = None
        self.wait = True
        self.reference_ts_old = []
        self.reference_ts_new = []  # To-Do: combine to one reference-info
        self.reference_ts_old_setted = False

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
            web_port=config["web_port"],
            id=config['id'],
            broker=config['broker'])
        return app

    def synchron(self, data: list, sensor: str):
        """
        This function is used when the sensor method is None.
        The data will not be cached, but forwarded synchronously without any aggregation.
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

    def _calc_ref_ts(self, last_ts: datetime.timestamp, cur_ts: datetime.timestamp):
        """
        This function is used to determine the next timestamp for the new window
        """
        mod = (last_ts.timestamp() - cur_ts.timestamp()) % (float(self.window.split('s')[0]))
        new_ts = last_ts.timestamp() - mod + float(self.window.split('s')[0])

        return datetime.fromtimestamp(new_ts)

    def aggregate(self, data: list, sensor: str):
        """
        This function is used to aggregate the given data depending on the given method.
        """
        if len(data) > 1:
            if datetime.strptime(data[-1]['timestamp'], "%Y-%m-%dT%H:%M:%S.%f") \
                    > self.reference_ts_new['data'][sensor]:
                self.wait = False
                self.reference_ts_old['data'][sensor] = self.reference_ts_new['data'][sensor]
                self.reference_ts_new['data'][sensor] = self._calc_ref_ts(
                    datetime.strptime(data[-1]['timestamp'], "%Y-%m-%dT%H:%M:%S.%f"),
                    self.reference_ts_old['data'][sensor])

                data_df = pd.DataFrame(data)
                data_df['timestamp'] = pd.to_datetime(data_df['timestamp'],
                                                      format="%Y-%m-%dT%H:%M:%S.%f")

                agg_data = data_df[data_df['timestamp'] <= self.reference_ts_old['data'][sensor]]

                non_agg_size = len(data_df) - len(agg_data)

                agg_data.index = agg_data['timestamp']

                if non_agg_size == 0:
                    self.iter_data['data'][sensor] = []
                else:
                    self.iter_data['data'][sensor] = data[-non_agg_size:]

                agg_data = agg_data.groupby(
                    pd.Grouper(freq=self.window,
                               origin=pd.Timestamp(self.reference_ts_old['data'][sensor]))).aggregate(
                    self.method)
                agg_data['timestamp'] = agg_data.index
                agg_data['timestamp'].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")

                self.ret_data['data'][sensor] = agg_data.to_dict('records')

    def _clean_ret_data(self):
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _clean_ts_ref_values(self):
        for sensor in self.reference_ts_old['data']:
            self.reference_ts_old['data'][sensor] = None
            self.reference_ts_new['data'][sensor] = None

    @staticmethod
    def _calc_modulo(data_size: int, window_size: int):
        """
        Doc TO-DO

        Parameters
        ----------
        data_size : TYPE
            DESCRIPTION.
        window_size : TYPE
            DESCRIPTION.

        Returns
        -------
        mod : TYPE
            DESCRIPTION.

        """
        mod = data_size % window_size
        return mod

    def _process(self, data: dict):
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

            # If iter_data is not empty, than extend the sensor values with the incoming data.
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

                if not self.reference_ts_old_setted \
                        and self.reference_ts_old['data'][sensor] is None:
                    first_ts = self.iter_data['data'][sensor][0]['timestamp']
                    ref_ts = datetime.fromtimestamp(
                        datetime.strptime(first_ts, "%Y-%m-%dT%H:%M:%S.%f").timestamp() + float(
                            self.window.split('s')[0]))
                    self.reference_ts_new['data'][sensor] = ref_ts

                if self.method is None:
                    self.synchron(self.iter_data['data'][sensor], sensor)
                else:
                    self.aggregate(self.iter_data['data'][sensor], sensor)

            if None not in self.reference_ts_old['data'].values():
                self.reference_ts_old_setted = True

        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            log.logging.error(self.error)
        if not self.wait:
            self.wait = True
            return self.ret_data
        else:
            return None

    def process(self, app: faust.App):
        """
        :param app: Faust app.
        """
        source_topic = app.topic(self._source_topic)
        aggregated_topic = app.topic(self._aggregated_topic)
        log.logging.info("Source Topic", source_topic)

        @app.agent(source_topic)
        async def stream_aggregate(stream):
            """Process incoming events from the source topics."""
            async for event in stream:
                res = self._process(event)
                if res:
                    await aggregated_topic.send(value=res)

if __name__ == '__main__':
    mode_path = r"./configs/config.json"
    with open(mode_path) as json_file:
        config = json.load(json_file)
        json_file.close()
    Agg = Aggregator(config)
    app = Agg.create_app(config['faust_config'])
    Agg.process(app)
    app.main()
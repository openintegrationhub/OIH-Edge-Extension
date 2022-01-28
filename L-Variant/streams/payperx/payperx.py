# -*- coding: utf-8 -*-
"""
Created on Thur Oct 14 2021
Pay-Per-X Component as Faust Stream

@author: AUS
"""
import logging
import json
import pandas as pd
import copy
from datetime import datetime
import traceback
import faust



class PayPerX:
    def __init__(self, config):
        #super().__init__(config)
        self.config = config
        self._source_topic=self.config['source_topic']
        self._aggregated_topic = self.config['aggregated_topic']
        self.interval = self.config['interval']
        self.bufferType = self.config['bufferType']
        self.nodesets = self.config['nodesets']
        self.pricePerkWh = self.config['kWh']
        self.pricePerStk = self.config['stk']
        self.interest_nodes = []
        for l in self.nodesets:
            self.interest_nodes = self.interest_nodes + l
        self.buffer = []
        self.stk = 0
        self.risk = 0
        self.price = 0
        self.logger = logging.getLogger()
        self.last_ts = {}
        self.reference_ts_new = None
        self.iter_data = {}
        self.ret_data = []
        self.wait = True

    def _synchron(self, data, sensor):
        """
            This function is used when method is None.
            The data will not be cached, but forwarded synchronously.
        :param data: dict
        :param sensor: sensor_field
        :return:
            None
        """
        self.wait = False
        self.iter_data['data'][sensor] = []
        self.ret_data['data'][sensor] = data

    def _clean_ret_data(self):
        """
            This function clears the return data values without deleting its structure.
        """
        for sensor in self.ret_data['data']:
            self.ret_data['data'][sensor].clear()

    def _calculate(self, data):
        """
            In this function the given data will be wrapped into DataFrame and will be forwarded to the
            in the config specified function. The Data will either be given by the iter_data field, or will
            be query'd from the influxdb.
        :param data: dict
        :param sensor: sensor_field
        :return:
            None
        """
        try:
            if datetime.strptime(data, "%Y-%m-%dT%H:%M:%S.%f") > self.reference_ts_new:
                self.wait = False

                for nset in self.nodesets:
                    if self.last_ts[nset[0]] <= self.last_ts[nset[1]]:
                        ts_d = self.last_ts[nset[0]]
                    else:
                        ts_d = self.last_ts[nset[1]]

                    tmp_df01 = pd.DataFrame(self.iter_data['data'][nset[0]]).rename(columns={"value": nset[0]})
                    tmp_df02 = pd.DataFrame(self.iter_data['data'][nset[1]]).rename(columns={"value": nset[1]})

                    tmp_df01['timestamp'] = pd.to_datetime(tmp_df01['timestamp'], format="%Y-%m-%dT%H:%M:%S.%f")
                    tmp_df02['timestamp'] = pd.to_datetime(tmp_df02['timestamp'], format="%Y-%m-%dT%H:%M:%S.%f")

                    # get the Data out of the DataFrame of the given Time
                    if tmp_df01['timestamp'][(len(tmp_df01) - 1)] <= tmp_df02['timestamp'][(len(tmp_df02) - 1)]:
                        ts_up = tmp_df01['timestamp'][len(tmp_df01) - 1]
                    else:
                        ts_up = tmp_df02['timestamp'][len(tmp_df02) - 1]

                    tmp01 = tmp_df01[ts_up >= tmp_df01['timestamp']]
                    tmp01 = tmp01[tmp01['timestamp'] >= ts_d].drop_duplicates()
                    tmp02 = tmp_df02[ts_up >= tmp_df02['timestamp']]
                    tmp02 = tmp02[tmp02['timestamp'] >= ts_d].drop_duplicates()

                    agg_data = pd.concat([tmp01, tmp02], axis=1)
                    agg_data = agg_data.loc[:, ~agg_data.columns.duplicated()]

                    # Setting last_ts to the last aggregated point
                    for sensor in nset:
                        self.last_ts[sensor] = agg_data['timestamp'][len(agg_data) - 1]

                    # Removes the aggregated data from the given data
                    for sensor in nset:
                        non_agg_size = len(self.iter_data['data'][sensor]) - len(agg_data)
                        if non_agg_size == 0:
                            self.iter_data['data'][sensor] = []
                        else:
                            self.iter_data['data'][sensor] = self.iter_data['data'][sensor][-non_agg_size:]

                    if any(pd.isna(agg_data)):
                        for data in agg_data.iloc:
                            i = 0
                            for d in data:
                                if pd.isna(d) == True:
                                    i += 1
                                    break
                            else:
                                i += 1
                                continue
                            break
                        agg_data.fillna(method='ffill', inplace=True)

                        agg_data = agg_data.drop(index=i)

                    self._calcSet(agg_data, nset)
                    self._calcRiskIndex(agg_data, nset[0])

                total = self.price + self.risk
                self.ret_data['data']['totalPrice'] = [
                    {'timestamp': str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")), 'value': total}]
                # Adjusting Window
                self.reference_ts_new = datetime.fromtimestamp(
                    self.reference_ts_new.timestamp() + float(self.interval + 1))
        except Exception as error:
            self.error = str(__class__) + ": " + str(error)
            self.logger.error(traceback.format_exc())

    def _calcSet(self, dataFrame, nset):
        try:
            dataFrame.mask(dataFrame == float('nan'), 1)
            self.logger.debug("dataFrame: %s", dataFrame)
            x = dataFrame[nset[0]] * dataFrame[nset[1]]
            x = x[1:]
            last = None
            s = []
            for data in dataFrame.iloc:
                try:
                    cur = datetime.strptime(data['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    cur = datetime.strptime(data['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
                except TypeError:
                    cur = data['timestamp']
                if last is not None:
                    s.append(float(cur.timestamp() - last.timestamp()) / 3600)
                last = cur

            kwh = x * s

            self.ret_data['data']['kWh'].append({'timestamp': str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")), 'value': sum(kwh)/1000})
            self.price += float((sum(kwh) / 1000) * self.pricePerkWh)
            self.ret_data['data']['kWhPrice'].append({'timestamp': str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")), 'value': self.price})
        except Exception as error:
            self.error = str(__class__) + ": " + str(error)
            self.logger.error(traceback.format_exc())

    def _calcRiskIndex(self, dataFrame, sensor):
        """
            This function is used to specify the riskIndex, in
            depending on the threshold given in the config
        :param
            data: DataFrame
        :return:
            index: float
        """
        try:
            last = 0
            for data in dataFrame.iloc:
                cur = data[sensor]
                if last != 0:
                    if cur < last:
                        self.stk += 1
                        self.risk = self.stk * self.pricePerStk
                last = cur
            self.ret_data['data']['risk'].append(
                {'timestamp': str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")), 'value': self.stk})
            self.ret_data['data']['risk'].append(
                {'timestamp': str(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")), 'value': self.risk})
        except Exception as error:
            self.error = str(__class__) + ": " + str(error)
            self.logger.error(traceback.format_exc())

    def _clean_iter_data(self):
        for sensor in self.iter_data['data']:
            self.iter_data['data'][sensor].clear()

    def _initialize_iter_data(self, data):
        """
            Ignore for now
        :return:
        """
        self.iter_data = {'data': {}}
        for sensor in self.interest_nodes:
            if sensor in data['data']:
                self.iter_data['data'][sensor] = data['data'][sensor]

    def _process(self, data):
        try:
            # initializing ret_data or cleans the previous ret_data
            if len(self.ret_data) == 0:
                self.ret_data = copy.deepcopy(data)
                self._clean_ret_data()
                self.ret_data['data']['kWh'] = []
                self.ret_data['data']['kWhPrice'] = []
                self.ret_data['data']['risk'] = []
                self.ret_data['data']['Stueck'] = []
            else:
                self._clean_ret_data()

            # Either initializes iter_data or extends it if it is not empty
            if len(self.iter_data) == 0:
                self._initialize_iter_data(data)
            else:
                for sensor in data['data'].keys():
                    if sensor in self.iter_data['data'] and sensor in self.interest_nodes:
                        self.iter_data['data'][sensor].extend(data['data'][sensor])

            # appends missing sensors, if they weren't in data as this component got initialized
            for sensor in self.interest_nodes:
                if sensor not in self.iter_data['data'] and sensor in data['data']:
                    self.iter_data['data'][sensor] = data['data'][sensor]
                    self.last_ts[sensor] = datetime.strptime(self.iter_data['data'][sensor][0]['timestamp'],
                                                             "%Y-%m-%dT%H:%M:%S.%f")

            for sensor in self.iter_data['data']:
                if sensor in self.interest_nodes and self.iter_data['data'][sensor]:
                    # setting the first timestamp
                    if self.reference_ts_new is None:
                        first_ts = self.iter_data['data'][sensor][0]['timestamp']
                        ref_ts = datetime.fromtimestamp(
                            datetime.strptime(first_ts, "%Y-%m-%dT%H:%M:%S.%f").timestamp() + float(self.interval))
                        self.reference_ts_new = ref_ts

                    if self.last_ts == {}:
                        for sens in self.interest_nodes:
                            self.last_ts[sens] = datetime.strptime(self.iter_data['data'][sens][0]['timestamp'],
                                                                   "%Y-%m-%dT%H:%M:%S.%f")
                    self._calculate(self.iter_data['data'][sensor][-1]['timestamp'])
            # Clear buffer if not inMemory buffering
            if self.bufferType['mode'] == "query":
                self._clean_iter_data()
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error(traceback.format_exc())

        if not self.wait:
            self.wait = True
            return self.ret_data
        else:
            return None

    def process(self, app):

        source_topic = app.topic(self._source_topic)
        aggregated_topic = app.topic(self._aggregated_topic)


        @app.agent(source_topic)
        async def stream_aggregate(stream):
            """Process incoming events from the source topics."""
            async for event in stream:
                res = self._process(event)
                if res:
                    await aggregated_topic.send(value=res)

    def create_app(self,config):
        """Create and configure a Faust based kafka-aggregator application.
        Parameters
        ----------
        config : `Configuration`, optional
            The configuration to use.  If not provided, the default
            :ref:`Configuration` will be used.
        """

        print("Kafka Broker is", config['broker'])
        app = faust.App(
            web_port=config["web_port"],
            id=config["id"],
            broker=config["broker"])

        return app

if __name__ == '__main__':
    mode_path = r"./config/config.json"
    with open(mode_path) as json_file:
        config = json.load(json_file)
        json_file.close()

    ppx = PayPerX(config["payperx_config"])
    app: faust.App = ppx.create_app(config["faustapp_config"])
    ppx.process(app)
    app.main()

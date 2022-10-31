# -*- coding: utf-8 -*-
"""
Created on Thur Oct 14 2021
Pay-Per-Use Component as Faust Stream

@author: AUS
"""
import logging
import signal
from datetime import datetime

import pandas as pd
from component_base_class.component_base_class import ComponentBaseClass
from pandas import DataFrame


class PayPerUse(ComponentBaseClass):
    """
        This class is used to calculate certain Pay-Per-Use Indices.

        Variables:
        ----------
            config (dict): given configuration for the PayPerUse-Component

            window_size (int): given by the config. The window_size describes
            the time intervals at which this class determines the new indices.

            node_sets (list): nested list of nodeIds, which are used to
            determine the indices.

            price_per_consumption (float): consumption price given by the
            config.

            price_per_unit (float): unit price given by the config.

            min_acceptance (float): minimum acceptance given by the config.

            risk_costs (float): risk costs given by the config.

            fix_costs (float): fix costs given by the config.

            interest_nodes (list): a list of NodeIds, which are used to
            determine the indices.

            quantity (int): number of pieces, determined by this class.

            price (float): total price, determined by a certain set of indices.

            acc_consumption (float): accumulated consumption, determined by
            this class.

            acc_fix (float): accumulated fix costs, determined by this class.

            acc_risk (float): accumulated risk costs, determined by this class.

            logger (Logger): logger

            reference_ts_old (timestamp): references the time from the last
            calculation.

            reference_ts_new (timestamp):  references the time for the next
            calculation.

            iter_data (dict): inMemory Buffer

            ret_data (dict): return data, consists of the new calculated
            indices and the previous data, which was not used for the
            calculation

            wait (bool): if true (no calculation) return None, if false (new
            calculated indices) return ret_data
        """

    def __init__(self):
        """ Initializes PayPerUse class.

        Parameters:
        -----------
        config: dict
        User configuration of the PayPerUse Component
        e.g.

        code-block:: json

        {
            "payperuse": {
                "source_topic: "kafka_stream_component_ppu_source",
                "aggregated_topic": "kafka_source_component_ppu_sink",
                "window_size": 5,
                "node_sets": [["sensor01", "sensor02"],
                            ["sensor03", "sensor04"]],
                "price_per_consumption": 0.145,
                "price_per_unit": 0.1,
                "risk_costs": 200,
                "fix_costs": 0.5,
                "minimum_acceptance": 200
            },
            "faustapp_config": {
                "id": "payperuse05",
                "broker": "kafka://localhost:9092",
                "port": 6068
            }
        }
        """
        try:
            super().__init__()
        except Exception as error:
            print(f'Failure in Base Class, {error}')
            return
        self.logger = self.get_logger()
        config_template = {
            "payperuse_config": {
                'source_topic': "",
                'aggregated_topic': "",
                'window_size': "",
                'node_sets': [],
                'price_per_consumption': "",
                'price_per_unit': "",
                'fix_costs': "",
                'risk_costs': "",
                'minimum_acceptance': ""
            },
            "faustapp_config": {
                'broker': "",
                'id': ""
            }
        }
        self._source_topic = ''
        self._aggregated_topic = ''
        self.faust_config = {}
        self.app_config = {}
        self.iter_data = {}
        self.config = {}
        self.price_per_consumption = 0
        self.unprocessed_message = 0
        self.acc_consumption = 0
        self.price_per_unit = 0
        self.min_acceptance = 0
        self.window_size = 0
        self.risk_costs = 0
        self.fix_costs = 0
        self.quantity = 0
        self.acc_risk = 0
        self.acc_fix = 0
        self.price = 0
        self.interest_nodes = []
        self.node_sets = []
        self.logger = logging.getLogger()
        self.reference_ts_old = None
        self.reference_ts_new = None
        self.app = None
        self.wait = True
        self.ret_data = {
            'metadata': {
                'deviceID': ""
            },
            'data': {

            }
        }
        self.load_config(config_template)
        if self.app and not self.terminated:
            self.app.main()

    def load_config(self, config_template: dict = None, source: str = 'file'):
        """ Loads the config for the component, either from env variables
        or from a file. Also start up the config checker thread, which
        frequently checks if the config got changed.

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
                                   for keys in config_template.keys()):
                if all(keys in self.config['payperuse_config']
                       for keys in config_template['payperuse_config']) and \
                        all(keys in self.config['faustapp_config']
                            for keys in config_template['faustapp_config']):
                    self.app_config = self.config['payperuse_config']
                    self.faust_config = self.config['faustapp_config']
                    self.window_size = self.app_config['window_size']
                    self.node_sets = self.app_config['node_sets']
                    self.interest_nodes = []
                    for nodes in self.node_sets:
                        self.interest_nodes = self.interest_nodes + nodes
                    self.price_per_consumption = self.app_config[
                        'price_per_consumption']
                    self.price_per_unit = self.app_config['price_per_unit']
                    self.min_acceptance = self.app_config['minimum_acceptance']
                    self.risk_costs = self.app_config['risk_costs']
                    self.fix_costs = self.app_config['fix_costs']
                    if self._source_topic != self.app_config['source_topic'] \
                            or self._aggregated_topic != self.app_config[
                        'aggregated_topic']:
                        self._source_topic = self.app_config['source_topic']
                        self._aggregated_topic = self.app_config[
                            'aggregated_topic']
                        self.app = self.create_app(self.faust_config)
                        self.create_agent(self._source_topic,
                                          self._aggregated_topic,
                                          self.app,
                                          self._process)
                    else:
                        self.logger.error('Missing key(s) in config')
                        print('Missing key(s) in config', flush=True)
                        self.terminated = True
                        return
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

    def _clean_ret_data(self):
        """ Either initialize ret_data or clears ret_data
        without deleting its structure.

        :return None
        """
        if not self.ret_data['data']:
            self.ret_data['data']['Consumption/Quantity'] = []
            self.ret_data['data']['Fix/Quantity'] = []
            self.ret_data['data']['Risk/Quantity'] = []
            self.ret_data['data']['Current Consumption'] = []
            self.ret_data['data']['Accumulated Consumption'] = []
            self.ret_data['data']['Quantity'] = []
            self.ret_data['data']['Consumption Price'] = []
            self.ret_data['data']['Fix costs'] = []
            self.ret_data['data']['Risk costs'] = []
            self.ret_data['data']['Total Price'] = []
            self.ret_data['data']['Price/Unit'] = []
        else:
            for sensor in self.ret_data['data']:
                self.ret_data['data'][sensor].clear()

    def create_data_frame(self, data: dict):
        """ Create a dataframe of the given data

        :param data: Given data
        :return: Dataframe
        """
        frames = []
        for sensor in data['data']:
            df_i = pd.DataFrame(
                data['data'][sensor]).rename(
                columns={'value': sensor})
            df_i.set_index('timestamp', inplace=True)
            # df_i.drop_duplicates(inplace=True)
            frames.append(df_i)

        # Merging Dataframes
        agg_data = pd.concat(frames, axis=1)
        agg_data.reset_index(inplace=True)
        agg_data = agg_data.rename(columns={'index': 'timestamp'})
        agg_data.sort_values(by='timestamp', inplace=True)

        # Get data from the given window_size
        agg_data = agg_data[pd.to_datetime(
            agg_data['timestamp']) <= pd.to_datetime(
            self.reference_ts_new)]

        return agg_data

    def calculate(self, current_timestamp: str):
        """ Given data will be wrapped into a Dataframe and will then
        be used to calculate the price in regard to a fix formula.

        :param current_timestamp: latest timestamp of the given data
        :return: None
        """
        while datetime.strptime(current_timestamp,
                                "%Y-%m-%dT%H:%M:%S.%f") \
                > self.reference_ts_new:
            self.wait = False
            now = datetime.strptime(
                self.iter_data['data'][self.interest_nodes[0]][0][
                    'timestamp'], "%Y-%m-%dT%H:%M:%S.%f")

            agg_data = self.create_data_frame(self.iter_data)

            agg_data.ffill(inplace=True)
            agg_data = pd.concat([agg_data[:1], agg_data[1:].dropna()])
            agg_data.reset_index(drop=True, inplace=True)

            # Setting reference_ts_old to the last aggregated point
            self.reference_ts_old = pd.to_datetime(
                agg_data['timestamp'][len(agg_data) - 1])

            for node in self.interest_nodes:
                # Removes the aggregated data from the given data
                non_agg_size = len(self.iter_data['data'][node]) - len(
                    agg_data[node])
                if non_agg_size == 0:
                    self.iter_data['data'][node] = [{
                        'timestamp': agg_data.iloc[-1, 0],
                        'value': agg_data.iloc[-1][node]}]
                else:
                    append_data = self.iter_data['data'][node][
                                  -non_agg_size - 1:]
                    append_data[0]['value'] = \
                        agg_data.iloc[-1][node]
                    self.iter_data['data'][node] = append_data

            agg_data.iloc[:, 1:] = agg_data.iloc[:, 1:].astype(float)

            # calculate price
            consumption, fix = self.calc_use(agg_data)
            acc_risk = self.calc_risk_index(agg_data)

            self.acc_consumption += consumption
            self.price += float(consumption * self.price_per_consumption)
            self.acc_fix += fix
            total = self.price + acc_risk + self.acc_fix

            if self.quantity != 0:
                price_per_unit = total / self.quantity
                consumption_quantity = self.price / self.quantity
                fix_quantity = self.acc_fix / self.quantity
                risk_quantity = acc_risk / self.quantity
            else:
                price_per_unit = total
                consumption_quantity = self.price
                fix_quantity = self.acc_fix
                risk_quantity = acc_risk

            self.ret_data['data']['Consumption/Quantity'].append(
                {'timestamp': str(now),
                 'value': float(consumption_quantity)})
            self.ret_data['data']['Fix/Quantity'].append(
                {'timestamp': str(now), 'value': float(fix_quantity)})
            self.ret_data['data']['Risk/Quantity'].append(
                {'timestamp': str(now), 'value': float(risk_quantity)})
            self.ret_data['data']['Current Consumption'].append(
                {'timestamp': str(now), 'value': float(consumption)})
            self.ret_data['data']['Accumulated Consumption'].append(
                {'timestamp': str(now),
                 'value': float(self.acc_consumption)})
            self.ret_data['data']['Quantity'].append(
                {'timestamp': str(now), 'value': float(self.quantity)})
            self.ret_data['data']['Consumption Price'].append(
                {'timestamp': str(now), 'value': float(self.price)})
            self.ret_data['data']['Fix costs'].append(
                {'timestamp': str(now), 'value': float(self.acc_fix)})
            self.ret_data['data']['Risk costs'].append(
                {'timestamp': str(now), 'value': float(acc_risk)})
            self.ret_data['data']['Total Price'].append(
                {'timestamp': str(now), 'value': float(total)})
            self.ret_data['data']['Price/Unit'].append(
                {'timestamp': str(now), 'value': float(price_per_unit)})

            # Adjusting Window
            self.reference_ts_new = datetime.fromtimestamp(
                self.reference_ts_new.timestamp()
                + float(self.window_size))

    def calc_use(self, data_frame: DataFrame) -> [int, int]:
        """ Determine the consumption and the fix price based on the data of
        the node sets.

        :param data_frame: Buffered data wrapped into a DataFrame
        :return: array with calculated consumption and the fix price
        """
        duration = pd.to_datetime(data_frame.timestamp).diff()
        duration = duration.dt.total_seconds()
        consumption = 0

        for nodeset in self.node_sets:
            voltage = data_frame[nodeset[0]] * data_frame[nodeset[1]]
            consumption += sum(voltage[1:] * (duration[1:] / 3600)) / 1000

        fix_price = sum(duration[1:] * self.fix_costs)
        return consumption, fix_price

    def calc_risk_index(self, data_frame: DataFrame):
        """ Determine the quantity and the accumulated risk of the given data,
        with regard to the node sets.

        :param data_frame: Buffered data wrapped into a DataFrame
        :return: accumulated risk
        """
        diff = data_frame.iloc[:, 1].diff() < 0
        self.quantity += sum(diff)

        if self.min_acceptance >= self.quantity:
            acc_risk = self.risk_costs \
                       * (1 - (self.quantity / self.min_acceptance))
        else:
            acc_risk = 0

        return acc_risk

    def _clean_iter_data(self):
        """ Clears the iter_data, without deleting its structure.

        :return None
        """
        for sensor in self.iter_data['data']:
            self.iter_data['data'][sensor].clear()

    def _initialize_iter_data(self, data: dict):
        """ Initialize iter_data in regards to the interest nodes.

        :param data: Incoming data stream
        :return: None
        """
        self.iter_data = {'data': {}}
        for sensor in self.interest_nodes:
            if sensor in data['data']:
                self.iter_data['data'][sensor] = data['data'][sensor]

    def _process(self, data: dict) -> dict:
        """ Processes the incoming data.

        :param data: Incoming data stream
        :return: Output data
        """
        try:
            # initializing ret_data or cleans the previous ret_data
            self._clean_ret_data()

            # Either initializes iter_data or extends it if it is not empty
            if len(self.iter_data) == 0:
                self._initialize_iter_data(data)
            else:
                for sensor in data['data'].keys():
                    if sensor in self.iter_data['data']:
                        self.iter_data['data'][sensor].extend(data['data'][
                                                                  sensor])
                    elif sensor in self.interest_nodes:
                        self.iter_data['data'][sensor] = data['data'][sensor]

            sensor = self.interest_nodes[0]

            # setting the first timestamp
            if self.reference_ts_new is None:
                first_ts = self.iter_data['data'][sensor][0]['timestamp']
                ref_ts = datetime.fromtimestamp(
                    datetime.strptime(first_ts,
                                      "%Y-%m-%dT%H:%M:%S.%f").timestamp()
                    + float(self.window_size))
                self.reference_ts_new = ref_ts

            if self.reference_ts_old is None:
                self.reference_ts_old = datetime.strptime(
                    self.iter_data['data'][sensor][0]['timestamp'],
                    "%Y-%m-%dT%H:%M:%S.%f")
            if all(sens in self.iter_data['data'] for sens in
                   self.interest_nodes):
                self.calculate(self.iter_data['data'][sensor][-1]['timestamp'])
        except ValueError as val_err:
            self.logger.warning('Invalid timestamp format')
            self.logger.error(val_err)
            self.unprocessed_message += 1
        except KeyError as key_err:
            self.logger.error(f'Invalid Configuration, {key_err}')
            signal.raise_signal(signal.SIGTERM)
        except Exception as error:
            self.logger.error(f'Error: {error} in process')
            signal.raise_signal(signal.SIGTERM)

        if not self.wait:
            self.wait = True
            return self.ret_data


if __name__ == '__main__':
    ppu = PayPerUse()

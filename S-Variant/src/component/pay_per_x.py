""" -*- coding: utf-8 -*-
Created on Thur Oct 14 2021
PayPerX Component of the On-Edge Adapter.
"""

__author__ = "TMO"

import copy
import logging
import traceback
from datetime import datetime

from influxdb import DataFrameClient
import pandas as pd

from component.component_base_class import ComponentBaseClass

datetime.utcnow()


class PayPerX(ComponentBaseClass):
    """
    This class is used to calculate certain Pay-Per-Use Indices.

    Variables:
    ----------
        config (dict): given configuration for the PayPerX-Component

        window_size (int): given by the config. The window_size describes
        the time intervals at which this class determines the new indices.

        buffer_type (dict): given by the config. It either uses inMemory
        buffering or it queries the data from an InfluxDB

        client (DataFrameClient): its only use is to query the data from an
        InfluxDB, if the query buffer_type is used.

        node_sets (list): nested list of nodeIds, which are used to determine
        the indices.

        price_per_consumption (float): consumption price given by the config.

        price_per_unit (float): unit price given by the config.

        min_acceptance (float): minimum acceptance given by the config.

        risk_costs (float): risk costs given by the config.

        fix_costs (float): fix costs given by the config.

        interest_nodes (list): a list of NodeIds, which are used to
        determine the indices.

        quantity (int): number of pieces, determined by this class.

        price (float): total price, determined by a certain set of indices.

        acc_consumption (float): accumulated consumption, determined by this
        class.

        acc_fix (float): accumulated fix costs, determined by this class.

        acc_risk (float): accumulated risk costs, determined by this class.

        logger (Logger): logger

        reference_ts_old (timestamp): references the time from the last
        calculation.

        reference_ts_new (timestamp):  references the time for the next
        calculation.

        iter_data (dict): inMemory Buffer

        ret_data (dict): return data, consists of the new calculated indices
        and the the previous data, which was not used for the calculation

        wait (bool): if true (no calculation) return None, if false (new
        calculated indices) return ret_data
    """

    def __init__(self, config: dict):
        """ Initializes PayPerX class.

        Parameters:
        -----------
        config: dict
        User configuration of the PayPerX Component
        e.g.

        code-block:: json

        {
            "name": "payperx",
            "config": {
                "window_size": 10,
                "buffer_type": {
                    "mode": "query/inMemory",
                    "host": "influxdb",
                    "port": "8086",
                    "db": "raw_data"
                    "queryFrom": "db.autogen.raw_data",
                    "username": "admin",
                    "password": "admin"
                },
                "nodesets":	[["ns=3;i=1004", "ns=3;i=1005"], ["ns=3;i=1002",
                "ns=3;i=1003"]],
                "price_per_consumption": 0.145,
                "price_per_unit": 0.1,
                "fix_costs": 0.0031623,
                "risk_costs": 200,
                "minimum_acceptance": 5760
            }
        }
        """
        super().__init__(config)
        self.config = config
        self.window_size = self.config['window_size']
        self.buffer_type = self.config['buffer_type']
        if self.buffer_type['mode'] == "query":
            # Connects to the InfluxDB
            self.client = DataFrameClient(
                host=self.buffer_type['host'],
                port=self.buffer_type['port'],
                username=self.buffer_type['username'],
                password=self.buffer_type['password'])
        self.node_sets = self.config['node_sets']
        self.price_per_consumption = self.config['price_per_consumption']
        self.price_per_unit = self.config['price_per_unit']
        self.min_acceptance = self.config['minimum_acceptance']
        self.risk_costs = self.config['risk_costs']
        self.fix_costs = self.config['fix_costs']
        self.interest_nodes = []
        for nodes in self.node_sets:
            self.interest_nodes = self.interest_nodes + nodes
        self.quantity = 0
        self.price = 0
        self.acc_consumption = 0
        self.acc_fix = 0
        self.acc_risk = 0
        self.logger = logging.getLogger()
        self.reference_ts_old = None
        self.reference_ts_new = None
        self.iter_data = {}
        self.ret_data = {
            'metadata': {
                'deviceID': ""
            },
            'data': {

            }
        }
        self.wait = True

    def _synchron(self, data: dict):
        """This function is used to forward the incoming data.
        So the given data might be used for other analytics components.

        Parameters:
        -----------
            data (dict): incoming data.
        """
        for sensor in data['data']:
            self.ret_data['data'][sensor] = data['data'][sensor]

    def _clean_ret_data(self):
        """This function either initializes ret_data or clears
        the ret_data values without deleting its structure.
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

    def _calculate(self, current_timestamp: str):
        """In this function the given data will be wrapped into a DataFrame,
        either from an InfluxDB or from the internal Buffer. This DataFrame
        is used to calculate a Price with a fixed Formula.

        Parameters:
        -----------
            current_timestamp (str): str of a sensor timestamp

        Returns:
        --------
            None
        """
        try:
            while datetime.strptime(current_timestamp, "%Y-%m-%dT%H:%M:%S.%f")\
                    > self.reference_ts_new:
                self.wait = False
                now = self.reference_ts_new

                if self.buffer_type['mode'] == "inMemory":
                    frames = []
                    for sensor in self.iter_data['data']:
                        df_i = pd.DataFrame(
                            self.iter_data['data'][sensor]).rename(
                            columns={'value': sensor})
                        df_i.set_index('timestamp', inplace=True)
                        frames.append(df_i)

                    # Merging Dataframes
                    agg_data = pd.concat(frames, axis=1)
                    agg_data.reset_index(inplace=True)
                    agg_data = agg_data.rename(columns={'index': 'timestamp'})

                    # Get data from the given window_size
                    agg_data = agg_data[pd.to_datetime(self.reference_ts_old)
                                        <= pd.to_datetime(agg_data[
                                                              'timestamp'])]
                    agg_data = agg_data[pd.to_datetime(self.reference_ts_new)
                                        >= pd.to_datetime(agg_data[
                                                              'timestamp'])]

                    # Setting reference_ts_old to the last aggregated point
                    self.reference_ts_old = pd.to_datetime(
                        agg_data['timestamp'][len(agg_data) - 1])

                    # Removes the aggregated data from the given data
                    non_agg_size = len(self.iter_data[
                                           'data'][self.interest_nodes[0]]) \
                                   - len(agg_data)
                    if non_agg_size == 0:
                        self.iter_data['data'][self.interest_nodes[0]] = [
                            self.iter_data['data'][self.interest_nodes[0]][-1]]
                    else:
                        self.iter_data['data'][self.interest_nodes[0]] = \
                            self.iter_data['data'][self.interest_nodes[0]][
                            -non_agg_size - 1:]
                elif self.buffer_type['mode'] == "query":
                    # Creating query string
                    sensors = ''.join(str('"' + x + '",')
                                      for x in self.interest_nodes)
                    query = "SELECT " + sensors[:-1] + " FROM " \
                            + self.buffer_type['queryFrom'] \
                            + " WHERE time >= '" \
                            + str(self.reference_ts_old) \
                            + "' and time < '" \
                            + str(self.reference_ts_new) \
                            + "'"

                    # Polls the data from influxdb
                    queried_data = self.client.query(query)

                    # Converts the queried data into dataframe with the same
                    # structure as the given data
                    agg_data = queried_data[self.buffer_type['db']]

                    agg_data.reset_index(inplace=True)
                    agg_data = agg_data.rename(columns={'index': 'timestamp'})

                    # Setting reference_ts_old to the last aggregated point
                    try:
                        self.reference_ts_old = agg_data['timestamp'][
                            len(agg_data) - 1].strftime(
                            "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        self.reference_ts_old = agg_data[
                            'timestamp'][len(agg_data) - 1].strftime(
                            "%Y-%m-%dT%H:%M:%SZ")

                # calculating KPIs
                consumption, fix = self._calc_use(agg_data)
                self._calc_risk_index(agg_data, self.interest_nodes[1])

                self.acc_consumption += consumption
                self.price += float(consumption * self.price_per_consumption)
                self.acc_fix += fix
                total = self.price + self.acc_risk + self.acc_fix

                if self.quantity != 0:
                    price_per_unit = total / self.quantity
                    consumption_quantity = self.price / self.quantity
                    fix_quantity = self.acc_fix / self.quantity
                    risk_quantity = self.acc_risk / self.quantity
                else:
                    price_per_unit = total
                    consumption_quantity = self.price
                    fix_quantity = self.acc_fix
                    risk_quantity = self.acc_risk

                # return calculated KPIs
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
                    {'timestamp': str(now), 'value': float(self.acc_risk)})
                self.ret_data['data']['Total Price'].append(
                    {'timestamp': str(now), 'value': float(total)})
                self.ret_data['data']['Price/Unit'].append(
                    {'timestamp': str(now), 'value': float(price_per_unit)})

                # Adjusting Window
                self.reference_ts_new = datetime.fromtimestamp(
                    self.reference_ts_new.timestamp()
                    + float(self.window_size))
        except Exception as error:
            self.error = str(__class__) + ": " + str(error)
            self.logger.error(traceback.format_exc())

    def _calc_use(self, data_frame: pd.DataFrame) -> [int, int]:
        """This function calculates the Consumption based on the interest nodes
        and the fixprice.

        The formulas are:
            Consumption = curent * voltage * duration
            fixprice = fix * duration

        Parameters:
        -----------
            data_frame (DataFrame): Buffered data
        Returns:
        --------
             [int, int] calculated indices.
        """
        duration = pd.to_datetime(data_frame.timestamp).diff()
        duration = duration.dt.total_seconds()
        consumption = 0

        for nodeset in self.node_sets:
            voltage = data_frame[nodeset[0]] * data_frame[nodeset[1]]
            consumption += sum(voltage[1:] * (duration[1:] / 3600)) / 1000

        fix_price = sum(duration[1:] * self.fix_costs)
        return consumption, fix_price

    def _calc_risk_index(self, data_frame: pd.DataFrame, sensor: str):
        """This function determines the quantity and the accumulated risk
        of the given data. The quantity increases everytime the given data
        drops to 1. The accumulated risk is determined by the formula:
            riskCost * (1 - quantity/minimumAcceptance) # the minimum
            acceptance is given in the config.
        If the minimum acceptance is reached, the risk is equal to 0

        Parameters:
        -----------
            data_frame (DataFrame): Buffered data.
        """
        last = 0
        for data in data_frame.iloc:
            cur = data[sensor]
            if last != 0:
                if cur < last:
                    self.quantity += 1
            last = cur

        if self.min_acceptance >= self.quantity:
            self.acc_risk = self.risk_costs \
                            * (1 - self.quantity / self.min_acceptance)
        else:
            self.acc_risk = 0

    def _clean_iter_data(self):
        """This function clears iter_data. It is only used, for the query
        function.

        Returns:
        --------
            None.
        """
        for sensor in self.iter_data['data']:
            self.iter_data['data'][sensor].clear()

    def _initialize_iter_data(self, data: dict):
        """This function is used to initialize the iter_data "buffer".

        Parameters:
        -----------
            data (dict): incoming data.
        """
        self.iter_data = {'data': {}}
        for sensor in self.interest_nodes:
            if sensor in data['data']:
                self.iter_data['data'][sensor] = data['data'][sensor]

    def _process(self, data: dict) -> dict:
        """
            This function is used to process the given data.

        Parameters:
        -----------
            data (dict): incoming data.

        Returns:
        --------
            ret_data (dict): output data, with the structure shown in
            process.
        """
        try:
            # initializing ret_data or cleans the previous ret_data
            self._clean_ret_data()

            # Either initializes iter_data or extends it if it is not empty
            if len(self.iter_data) == 0:
                self._initialize_iter_data(data)
            else:
                for sensor in data['data'].keys():
                    if sensor in self.iter_data['data'] \
                            and sensor in self.interest_nodes:
                        self.iter_data['data'][sensor].extend(
                            data['data'][sensor])

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
                self.reference_ts_old = datetime \
                    .strptime(self.iter_data['data'][sensor][0]['timestamp'],
                              "%Y-%m-%dT%H:%M:%S.%f")
            self._synchron(copy.deepcopy(data))
            self._calculate(self.iter_data['data'][sensor][-1]['timestamp'])
            self.logger.debug("Hier %s", self.ret_data['data'])
            # Clear buffer if not inMemory buffering
            if self.buffer_type['mode'] == "query":
                self._clean_iter_data()
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error(traceback.format_exc())

        return self.ret_data

    def process(self, data: dict) -> dict:
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

        code-block:: json

        {
            'data':{
                'Consumption/Quantity': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Fix/Quantity': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'RiskQuantity': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Current Consumption': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Accumulated Consumption':
                [{'timestamp': '2020-06-20T16:12:54', 'value': x}],
                'Quantity': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Consumption Price': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Fix costs': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Risk costs': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Total Price': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}],
                'Price/Unit': [{'timestamp': '2020-06-20T16:12:54',
                'value': x}]
            }
        }
        """
        return self._process(data)

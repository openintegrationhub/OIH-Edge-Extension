# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020
"""

__author__ = 'TMO'

import asyncio
# EXAMPLE CONFIG
# {
#   "name": "opcua_producer",
#   "kafka_broker": "",
# 	"sink_topic": "opcua",
# 	"opcua_host": "opc.tcp://192.168.10.51:4840",
# 	"security": {
# 		"password": "user",
# 		"username": "user"
# 	},
# 	"time_out": 200,
#   "mode": "subscription",
#   "node_ids": [],
#   "check_time": 2000,
#   "discovery": true,
#   "discovery_config: {
#       "to_ignore": ["Views", "Type", "Server"],
#       "node_type": ["BaseDataVariableType"]
#   }
# }
import json
import logging
import logging.handlers
from concurrent.futures import TimeoutError as FuturesTimeoutError

import asyncua
from asyncua import Client
from asyncua import Node
from asyncua import ua
from asyncua.ua.uaerrors import BadIdentityTokenRejected
from asyncua.ua.uaerrors import BadNodeIdUnknown
from asyncua.ua.uaerrors import BadNotSupported
from component_base_class.component_base_class import ComponentBaseClass
from kafka import KafkaProducer


class OPCUAProducer(ComponentBaseClass):
    """
    This class serves as a Producer, which takes data from an OPCUA-Server
    and writes them into a specified kafka topic.
    """

    def __init__(self):
        """
        Constructor of the OPCUAProducer.
        """
        config_template = {
            "name": "",
            "opcua_host": "",
            "security": "",
            "time_out": "",
            "check_time": "",
            "sink_topic": "",
            "kafka_broker": "",
            "mode": "",
            "discovery": ""
        }
        try:
            super().__init__()
        except Exception:
            print('failure in base class')
            return
        self.logger_config = {}
        self.config = {}
        self.logger = self.get_logger()
        self.host = ''
        self.username = ''
        self.password = ''
        self.topic = ''
        self.kafka_broker = None
        self.db_checker = None
        self.producer = None
        self.client = None
        self.node_ids = []
        self.to_ignore = []
        self.node_type = []
        self.time_out = 0
        self.check_time = 0
        self.connected = False
        self.subscribed = False
        self.sub_nodes = []
        self.sub_nodes_id = []
        self.parent_id = {}
        self.sub = None
        self.sub_handle = None
        self.load_config(config_template)
        logging.getLogger('asyncua').setLevel('ERROR')
        logging.getLogger('asyncio').setLevel('WARNING')
        logging.getLogger('KafkaProducer').setLevel('WARNING')
        if not self.terminated:
            asyncio.run(self.run())

    def load_config(self, config_template: dict = None, source: str = 'file'):
        """ Loads the config for the component, either from env variables
        or from a file.

        :param config_template: dict with all required fields for the
        component to work.
        :param source: source of the config, either file or env
        :return: None
        """
        if source != 'file':
            config = self.get_config(
                config_template,
                source=source,
                file_path=f'/config/{self.path_name}')
        else:
            config = self.wait_for_config_insertion()
        self.config = config
        try:
            if self.config and all(key in self.config
                                   for key in config_template.keys()):
                if "username" in config['security'] and "password" in config[
                    'security']:
                    self.username = config['security']['username']
                    self.password = config['security']['password']
                self.check_time = config['check_time']
                self.time_out = config['time_out']
                if config['node_ids']:
                    self.node_ids = config['node_ids']
                self.host = config['opcua_host']
                self.kafka_broker = config['kafka_broker']
                self.producer = KafkaProducer(
                    bootstrap_servers=[self.kafka_broker])
                self.topic = config['sink_topic']
                if config['discovery_config']:
                    if 'to_ignore' in config['discovery_config'] \
                            and 'node_type' in config['discovery_config']:
                        self.to_ignore = config['discovery_config'][
                            'to_ignore']
                        self.node_type = config['discovery_config'][
                            'node_type']
                    else:
                        self.logger.error('Missing key(s) in discovery config')
                        print('Missing key(s) in discovery config', flush=True)
                        self.terminated = True
            else:
                self.logger.error('Missing key(s) in config')
                print('Missing key(s) in config', flush=True)
                self.terminated = True
        except Exception as error:
            self.logger.error(f'Error: {error} in load_config')
            self.terminated = True

    async def run(self):
        """ Main function of the opcua producer.

        :return: None
        """
        try:
            print('OPCUA-Producer starting...', flush=True)
            while not self.terminated:
                if not self.connected:
                    await self._connect()
                if not self.sub_nodes and self.connected:
                    await self.prepare_nodes()
                if self.config['mode'] == 'subscription':
                    if not self.subscribed and self.connected:
                        await self.subscribe_to_nodes()
                elif self.config['mode'] == 'polling':
                    await self.write_value()
                await asyncio.sleep(self.check_time / 1000)
                await self._check_connection()
        except Exception as error:
            self.logger.error(f'Error: {error} in run')
            self.terminated = True
        finally:
            if self.connected:
                await self.client.disconnect()
                self.logger.debug('Disconnected from OPCUA-Server')
            if self.producer.bootstrap_connected():
                self.producer.close()
                self.logger.debug('Closed Kafka Producer')
            print('OPCUA-Producer stoppped', flush=True)

    async def prepare_nodes(self):
        """ Fetches Nodes from the client and registers them, if supported by
        the server.

        :return: None
        """
        print('Preparing nodes...', flush=True)
        if self.node_ids:
            for node_id in self.node_ids:
                node = self.client.get_node(node_id)
                try:
                    await node.read_display_name()
                except BadNodeIdUnknown:
                    self.logger.warning(f'{str(node)} is invalid')
                    continue

                self.parent_id[node] = await node.get_parent()

                if self.config['discovery']:
                    await self.discovery(node)
                else:
                    self.sub_nodes.append(node)
        else:
            self.logger.warning(
                'No NodeIds given, continue discovery from root node!')
            await self.discovery(self.client.get_root_node())

        try:
            self.sub_nodes = await self.client.register_nodes(
                self.sub_nodes)
        except BadNotSupported:
            self.logger.warning('Server does not support to register nodes, '
                                'might result in poor performance')
        print('Nodes prepared', flush=True)

    async def _check_connection(self):
        """ This function is used to check the Connection to the OPC Server

        :return: None
        """
        try:
            node = self.client.get_root_node()
            await node.get_children()
            await node.read_attribute(ua.AttributeIds.NodeClass)
        except ConnectionRefusedError:
            self.connected = False
            self.subscribed = False
        except OSError:
            self.connected = False
            self.subscribed = False
        except FuturesTimeoutError:
            self.connected = False
            self.subscribed = False
        except AttributeError:
            self.connected = False
            self.subscribed = False

    async def _connect(self):
        """ Connects the Client to the OpcUaServer.
        Sign in as an anonymous user or with username and password.

        :return: None
        """
        try:
            print('Connecting to OPCUA-Server', flush=True)
            self.client = Client(self.host, self.time_out)
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)
            await self.client.connect()
            self.logger.debug('Connected to OPCUA-Server')
            self.connected = True
        except ConnectionRefusedError:
            self.connected = False
            self.subscribed = False
        except OSError:
            self.connected = False
            self.subscribed = False
        except FuturesTimeoutError:
            self.connected = False
            self.subscribed = False
        except AttributeError:
            self.connected = False
            self.subscribed = False
        except BadIdentityTokenRejected as invalid_identity:
            print('Invalid Credentials', flush=True)
            raise ValueError('Invalid Credentials') from invalid_identity

    async def subscribe_to_nodes(self):
        """ Initializes a sub handler and subscribes to the given
        nodes.

        :return: None
        """
        if not self.sub:
            self.sub = await self.client.create_subscription(
                period=self.check_time, handler=SubHandler(self))
        self.sub_handle = await self.sub.subscribe_data_change(self.sub_nodes)
        self.logger.debug(f'Subscribed to {len(self.sub_nodes)} Nodes')
        print(f'Subscribed to {len(self.sub_nodes)} Nodes', flush=True)
        self.subscribed = True

    async def write_value(self):
        """ Writes the value of the given nodes to the kafka broker.

        :return: None
        """
        if not self.sub_nodes_id:
            self.sub_nodes_id = [node.nodeid for node in self.sub_nodes]
        values = await self.client.uaclient.read_attributes(
            self.sub_nodes_id,
            ua.AttributeIds.Value
        )
        node_value_pairs = dict(zip(self.sub_nodes, values))

        data = {
            'data': {

            },
            'metadata': {

            }
        }
        for node in node_value_pairs:
            value_set = {
                'timestamp': node_value_pairs[
                    node].SourceTimestamp.strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"),
                'value': node_value_pairs[node].Value.Value
            }
            data['data'][str(node)] = [value_set]
        self.producer.send(
            self.topic,
            value=json.dumps(data).encode('UTF-8'),
        ).add_callback(self.on_broker_delivery)
        self.producer.flush()

    def on_broker_delivery(self, original_message):
        """ Callback of the kafka broker, if the message is successfully sent.

        :param original_message: message to be sent.
        :return: None
        """
        self.logger.debug(
            "Kafka broker received message: " + str(original_message))

    async def discovery(self, root_node: asyncua.Node):
        """ Iterate through the children nodes of the given node and find
        subscribable nodes, regarding the given data node_type.

        :param root_node: Given node to iterate through all children nodes.
        :return: None
        """
        if not self.terminated and self.connected:
            browse = await root_node.read_display_name()
            if any(browse.Text == variant.name for variant in
                   ua.uatypes.VariantType):
                return
            node_class = await root_node.read_node_class()
            children = await root_node.get_children()
            ref_list = await root_node.get_references(
                direction=ua.BrowseDirection.Forward)
            if root_node == self.client.get_root_node():
                for node in children:
                    await self.discovery(node)
            elif ua.NodeClass.Variable == node_class:
                if any(ref_list[0].BrowseName.Name == dType for dType in
                       self.node_type):
                    attr = await root_node.read_attributes(
                        [ua.AttributeIds.DataType])
                    if 0 < attr[0].Value.Value.Identifier < 12:
                        if await root_node.get_user_access_level() >= \
                                await root_node.get_access_level():
                            node_name = await root_node.read_display_name()
                            self.logger.debug(f'Node discovered: '
                                              f'{str(node_name)}')
                            self.sub_nodes.append(root_node)
                            self.parent_id[root_node] = await root_node \
                                .get_parent()
                for node in children:
                    await self.discovery(node)
            elif ref_list[0].BrowseName.Name == "FolderType":
                if any(browse.Text == name for name in self.to_ignore):
                    return
                elif "Views" == browse.Text:
                    return
                elif "Types" == browse.Text:
                    return
                elif "AccessLevels" == browse.Text:
                    return
                for node in children:
                    await self.discovery(node)
            elif ref_list[0].BrowseName.Name == "BaseObjectType":
                if any(browse.Text == name for name in self.to_ignore):
                    return
                if "Server" == browse.Text:
                    return
                for node in children:
                    await self.discovery(node)


class SubHandler():
    """
    This class handles the subscribed nodes.
    """

    def __init__(self, producer: OPCUAProducer):
        """ Constructor of the Subscription handler

        :param producer: instance of the opcua producer
        """
        self.opcua_producer = producer
        self.producer = producer.producer
        self.topic = producer.topic

    def datachange_notification(self, node: Node, val, data):
        """ This function handles the datachanges events of the subscribed
            nodes, it passes the node and the value to a function,
            which writes the data into the buffer.

        :param node: subscribed node
        :param val: value of the node
        :param data: data of the node
        :return:
        """
        try:
            self.opcua_producer.logger.debug(
                f'Python: New data change event on node {node}, with val '
                f'{val} and {str(data)}'
            )
            self.isList(node, val, data.monitored_item.Value.SourceTimestamp)
        except Exception as error:
            self.opcua_producer.logger.error(
                f"Error: {error}, in SubHandler datachange_notification")

    def isList(self, node, val, ts):
        """
            This function writes the value of the node into the buffer if it
            is a non-list object or if it is a list it calls the function again
            with the values of the list, until it is a non-list object.
        :param ts: timestamp of the given Value
        :param node: node to be written into the buffer
        :param val: either a list or a value to be written into the buffer
        :return:
        """
        if isinstance(val, list):
            for v in val:
                self.isList((node + " " + str(val.index(v))), v, ts)
        else:
            self.opcua_producer.data = {
                "metadata": {
                    "deviceID": ""
                },
                "data": {

                }
            }
            self.opcua_producer.data['metadata']['deviceID'] = str(
                self.opcua_producer.parent_id[node])
            self.opcua_producer.data['data'][str(node)] = []
            value_set = {'timestamp': ts.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                         'value': float(val)}
            self.opcua_producer.data['data'][str(node)].append(value_set)
            self.producer.send(
                self.topic,
                value=json.dumps(self.opcua_producer.data).encode('utf-8')) \
                .add_callback(self.on_broker_delivery)
            self.producer.flush()

    def on_broker_delivery(self, original_message):
        self.opcua_producer.logger.debug(
            f"Broker received message: {str(original_message)}")

    def status_change_notification(self, event):
        self.opcua_producer.logger.debug(f"Python: New Status event change "
                                         f"{event}")

    def event_notification(self, event):
        self.opcua_producer.logger.debug(f"Python: New event {event}")


if __name__ == '__main__':
    connector = OPCUAProducer()

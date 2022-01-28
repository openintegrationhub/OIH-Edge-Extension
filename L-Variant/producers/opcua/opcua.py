# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020

@author: AUS
"""
# EXAMPLE CONFIG
# {
#   "name": "opcua_producer",
#   "kafka_broker": "",
# 	"sink_topic": "opcua",
# 	"opcua_url": "opc.tcp://192.168.10.51:4840",
# 	"security": {
# 		"password": "user",
# 		"username": "user"
# 	},
# 	"timeOut": 200,
# 	"deviceid":"EMA-Tec",
#   "mode": {
#       "mode": "sub",
#       "discovery": "True",
#       "nodeids": ["ns=4;i=5001"], Je nach Mode kann man entweder die NodeId eines Sensors angeben oder eine Vater Node
#                   von denen man die Kinder Nodes subscriben/pollen will. discPol/discSub: Für RootNode leer lassen
#       "type": ["TagType"] #Default: "BaseDataVariableType",
#       "toIgnore": ["Views", "Types", "Server"], Folders and Objects to be Ignored while browsing through the
#                   Address Space
#       "subCheckTime"/"pol_time": 100/5 Je nach Modus: "discPol" und subCheckTime in Mili für
#                   "sub"/"discSub"/pol_time in Sek für "pol"
#   }
# }
import time
import datetime
import json
import asyncio
import logging
import logging.handlers
import threading

from concurrent.futures import TimeoutError as FuturesTimeoutError
from asyncua import ua, Client
from kafka import KafkaProducer


class OPCUAConnector:
    def __init__(self):
        """
            Pull all data from the config file and initialize all major data variables to ensure
            that the program runs without problems
        :param config: dict as shown above
        """
        try:
            super().__init__()
            # LOGGING-FORMATTER
            loggingFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %('
                                                 'message)s')
            # ERROR-HANDLER
            errorhandler = logging.handlers.RotatingFileHandler('./logs/error.log', maxBytes=1024 * 1024 * 2,
                                                                backupCount=9, delay=False)
            errorhandler.setLevel(logging.WARNING)
            errorhandler.setFormatter(loggingFormatter)
            # DEBUG-HANDLER
            debughandler = logging.handlers.RotatingFileHandler('./logs/debug.log', maxBytes=1024 * 1024 * 2,
                                                                backupCount=9, delay=False)
            debughandler.setLevel(logging.DEBUG)
            debughandler.setFormatter(loggingFormatter)
            # LOGGER
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(errorhandler)
            self.logger.addHandler(debughandler)

            mode_path = r"./config/config.json"
            with open(mode_path) as json_file:
                config = json.load(json_file)
                json_file.close()
            self.config = config
            self.error = None
            self.url = config['opcua_url']
            self.client = None
            if "username" and "password" in config['security']:
                self.username = config['security']['username']
                self.password = config['security']['password']
            self.deviceid = config['deviceid']
            self.timeOut = config['timeOut']
            if "pol" == config['mode']['mode']:
                self.pol_time = config['mode']['pol_time']
                self.nodeids = config['mode']['nodeids']
                if "True" == config['mode']['discovery']:
                    if "type" in config['mode']:
                        self.type = config['mode']['type']
                    else:
                        self.type = "BaseDataVariableType"
            elif "sub" == config['mode']['mode']:
                self.subCheckTime = config['mode']['subCheckTime']
                self.nodeids = config['mode']['nodeids']
                if "type" in config['mode']:
                    self.type = config['mode']['type']
                else:
                    self.type = "BaseDataVariableType"
            elif "methods" == config['mode']['mode']:
                self.args = config['mode']['args']
                self.nodeids = config['mode']['nodeids']
            if "toIgnore" in config['mode']:
                self.toIgnore = config['mode']['toIgnore']
            if "kafka_broker" and "sink_topic" in config:
                self.topic = config["sink_topic"]
                self.producer = KafkaProducer(bootstrap_servers=[config["kafka_broker"]])
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in __init__", error)
        self.data = {}
        self.dict = {}
        self.nodeCounter = 0
        self.interest_nodes = []
        self.gatherThreads = []
        self.subscribed = False
        self.connected = False
        self.sub = None
        self.info = None
        self.terminated = False
        self.error = None
        self.status = "start"
        self.run()

    def run(self):
        """
            This functions sole purpose is to start the
            programm as specified in the config.
        :return:
        """
        self.info = "OPCUAConnector started"
        self.logger.info("OPCUAConnector started")
        if "sub" == self.config['mode']['mode']:
            asyncio.run(self.query_subscription())
        elif "pol" == self.config['mode']['mode']:
            asyncio.run(self.query_pol())
        while not self.terminated:
            time.sleep(1)
        self.logger.info("OPCUAConnector stopping")
        self.info = "OPCUAConnector stopping"

    async def _checkConnection(self):
        """
            This function is used to check the Connection to the OPC Server
        :return:
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
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _checkConnection", error)
            if self.connected:
                await self.client.disconnect()

    async def _connect(self):
        """
            This function connects the Client to the OpcUaServer.
            Either u sign in as an anonymous user or with username and password or via security_string.
        :return:
            None.
        """
        try:
            self.client = Client(self.url, self.timeOut)
            if "username" and "password" in self.config['security']:
                self.client.set_user(self.username)
                self.client.set_password(self.password)
                await self.client.connect()
                self.logger.debug("Logged in as user %s.", self.username)
            else:
                await self.client.connect()
                self.logger.debug("Logged in as anonymous user.")
            self.connected = True
            await self.client.load_data_type_definitions()
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
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _connect", error)

    async def query_pol(self):
        """
            This function is used to poll create Task Objects, which polls
            data in given interval. It also starts the _connect function, which
            establishes a connection to the OPC UA Server and initializes all
            nodes given by the config.
        :return:
            None.
        :exception:
            This function raises a RuntimeException if there are no
            nodeids given in the config, when not using the discovery.
        """
        try:
            # Establish Connection
            await self._connect()
            if self.config['mode']['discovery'] == "False":
                if self.nodeids:
                    # Append all Nodes given via the config into a list
                    nodes = []
                    for nodeid in self.nodeids:
                        nodes.append(self.client.get_node(nodeid))
                    # Check if nodes already collected
                    if self.interest_nodes:
                        await self._write(nodes)
                else:
                    # Raise a RuntimeError, if no Nodes are given in the Config
                    raise RuntimeError
            elif self.config['mode']['discovery'] == "True":
                # If there are Nodeids given in the Config, call the _browse function with the given Node, otherwise use the rootNode
                if self.nodeids:
                    for nodeid in self.nodeids:
                        await self._browse(self.client.get_node(nodeid))
                else:
                    await self._browse(self.client.get_root_node())
                self.logger.debug("NodeCount: %s", self.nodeCounter)
                # Check if nodes already collected
                if self.interest_nodes:
                    await self._write(self.interest_nodes)
            if self.terminated and self.connected:
                await self.client.disconnect()
        except RuntimeError as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: No NodeIds given in non-discovery mode! %s", error)
            if self.connected:
                await self.client.disconnect()
        except (KeyboardInterrupt, SystemExit):
            if self.connected:
                await self.client.disconnect()
            self.terminated = True
            self.status = "stop"
            raise
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in query_pol", error)
            if self.connected:
                await self.client.disconnect()

    async def _write(self, nodes):
        """
            This function writes the value of the given node into the buffer,
            in given interval(pol_time).
        :param node: node
            node to be written into the buffer.
        :return:
            None.
        """
        try:
            while not self.terminated:
                while self.status == "start":
                    t = datetime.datetime.now().timestamp()
                    await self._checkConnection()
                    if not self.connected and not self.terminated:
                        await self._connect()
                    self.data = {
                        'metadata': {
                            'deviceID': ""
                        },
                        'data': {

                        }
                    }
                    value = await self.client.read_values(nodes)
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
                    pairs = dict(zip(nodes, value))
                    for pair in pairs:
                        self.data['metadata']['deviceID'] = str(await pair.get_parent())
                        self.data['data'][str(pair)] = []
                        valueset = {'timestamp': timestamp,
                                    'value': float(pairs[pair] if pairs[pair] is not None else 0)}
                        self.data['data'][str(pair)].append(valueset)
                    self.producer.send(
                        self.topic,
                        value=json.dumps(self.data).encode('utf-8'),
                        key=json.dumps(self.deviceid).encode('utf-8'))\
                        .add_callback(self.on_broker_delivery)
                    self.producer.flush()
                    t = datetime.datetime.now().timestamp() - t
                    #self.data['metadata']['deviceID'] = str(await node.get_parent())
                    # await self.isList(str(node), value)
                    await asyncio.sleep(float(self.pol_time)-t)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _write", error)
            if self.connected:
                await self.client.disconnect()

    def on_broker_delivery(self, err, decoded_message, original_message):
        if err is not None:
            print(err)
        self.logger.debug("Kafka broker received message: " + str(original_message))

    async def query_subscription(self):
        """
            This function is used to subscribe to a certain set of
            nodes given by the config. It first establishes a connection
            with the _connect function and initializes all nodes to be
            subscribed.
        :return:
            None.
        :exception:
            This function raises a RuntimeException if there are no
            nodeids given in the config, when not using the discovery.
        """
        try:
            await self._connect()
            while not self.terminated:
                if "False" == self.config['mode']['discovery'] and not self.subscribed:
                    if self.nodeids:
                        if not self.subscribed and self.connected and not self.interest_nodes:
                            for nodeid in self.nodeids:
                                self.interest_nodes.append(self.client.get_node(nodeid))
                                self.dict[self.client.get_node(nodeid)] = await self.client.get_node(nodeid).get_parent()
                    else:
                        raise RuntimeError
                elif "True" == self.config['mode']['discovery'] and not self.subscribed:
                    if not self.interest_nodes and self.connected:
                        if self.nodeids:
                            for nodeid in self.nodeids:
                                await self._browse(self.client.get_node(nodeid))
                        else:
                            await self._browse(self.client.get_root_node())
                        self.logger.debug("NodeCount: %s", self.nodeCounter)
                while self.status == "start":
                    await self._checkConnection()
                    if not self.connected and not self.terminated:
                        await self._connect()
                    if not self.subscribed:
                        await self._subscribe(self.interest_nodes)
                    if self.connected and self.subscribed:
                        await asyncio.sleep(1)
                if self.terminated:
                    if self.connected:
                        await self.client.disconnect()
        except RuntimeError as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: No NodeIds given, in non-discovery mode! %s", error)
            if self.connected:
                await self.client.disconnect()
        except (KeyboardInterrupt, SystemExit):
            if self.connected:
                await self.client.disconnect()
            self.terminated = True
            self.status = "stop"
            raise
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in query_subscription", error)
            if self.connected:
                await self.client.disconnect()

    async def _subscribe(self, nodes):
        """
            This function is used to create a subscription
             and also to subscribe to a given set of nodes
        :param nodes: a list containing nodes
        :return:
            None
        """
        try:
            if not self.subscribed and self.connected:
                if self.sub is None:
                    self.sub = await self.client.create_subscription(period=self.subCheckTime, handler=SubHandler(self))
                await self.sub.subscribe_data_change(nodes)
                await self.sub
                self.logger.debug("Added subscription to nodes %s", str(nodes))
                self.subscribed = True
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _subscribe", error)
            if self.connected:
                await self.client.disconnect()

    async def _browse(self, rootNode):
        """
            This function is used to subscribe to the children nodes of
            the given node.
        :param rootNode: given node to iterate through all children nodes.
        :return:
            None
        """
        try:
            if not self.terminated and self.connected:
                browse = await rootNode.read_display_name()
                nodeClass = await rootNode.read_node_class()
                children = await rootNode.get_children()
                reflist = await rootNode.get_references(direction=ua.BrowseDirection.Forward)
                if rootNode == self.client.get_root_node():
                    for node in children:
                        await self._browse(node)
                elif ua.NodeClass.Variable == nodeClass:
                    if any(reflist[0].BrowseName.Name == dType for dType in self.type):
                        attr = await rootNode.read_attributes([ua.AttributeIds.DataType])
                        # self.logger.debug("Hier %s", attr[0].Value.Value.Identifier)
                        if 0 < attr[0].Value.Value.Identifier < 12:
                            # if ua.ValueRank.Scalar == await rootNode.read_value_rank():
                            if await rootNode.get_user_access_level() >= await rootNode.get_access_level():
                                self.interest_nodes.append(rootNode)
                                self.dict[rootNode] = await rootNode.get_parent()
                                #self.logger.debug("%s appended", browse.Text)
                                self.nodeCounter += 1
                    for node in children:
                        await self._browse(node)
                elif reflist[0].BrowseName.Name == "FolderType":
                    if any(browse.Text == name for name in self.toIgnore):
                        return
                    elif "Views" == browse.Text:
                        return
                    elif "Types" == browse.Text:
                        return
                    elif "AccessLevels" == browse.Text:
                        return
                    for node in children:
                        await self._browse(node)
                elif reflist[0].BrowseName.Name == "BaseObjectType":
                    if any(browse.Text == name for name in self.toIgnore):
                        return
                    if "Server" == browse.Text:
                        return
                    for node in children:
                        await self._browse(node)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Node: %s", rootNode)
            self.logger.error("Error: %s, in browse", error)
            if self.connected:
                await self.client.disconnect()


class SubHandler(object):
    """
    This class handles the subscribed nodes.
    """

    def __init__(self, opcuaconnector: OPCUAConnector):
        self.connector = opcuaconnector
        self.producer = opcuaconnector.producer
        self.topic = opcuaconnector.topic

    def datachange_notification(self, node, val, data):
        """
            This function handles the datachanges events of the subscribed nodes,
            it passes the node and the value to a function, which writes the data
            into the buffer.
        :param node: subscribed node
        :param val: value of the node
        :param data: data of the node
        :return:
        """
        try:
            self.connector.logger.debug("Python: New data change event on node %s, with val: %s and data %s", node, val,
                                        str(data))
            self.isList(node, val, data.monitored_item.Value.SourceTimestamp)
        except Exception as error:
            self.connector.error = str(self.__class__) + ": " + str(error)
            self.connector.logger.error("Error: %s, in SubHandler datachange_notification", error)

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
            self.connector.data = {
                "metadata": {
                    "deviceID": ""
                },
                "data": {

                }
            }
            self.connector.data['metadata']['deviceID'] = str(self.connector.dict[node])
            self.connector.data['data'][str(node)] = []
            valueset = {'timestamp': ts.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                        'value': float(val)}
            self.connector.data['data'][str(node)].append(valueset)
            self.producer.send(
                self.topic,
                value=json.dumps(self.connector.data).encode('utf-8'),
                key=json.dumps(self.connector.deviceid.encode('utf-8')))\
                .add_callback(self.on_broker_delivery)
            self.producer.flush()

    def on_broker_delivery(self, err, decoded_message, original_message):
        if err is not None:
            print(err)
        self.connector.logger.debug("Broker received message: " + str(original_message))

    def status_change_notification(self, event):
        try:
            self.connector.logger.debug("Python: New Status event change %s", event)
        except Exception as error:
            self.connector.error = str(self.__class__) + ": " + str(error)
            self.connector.logger.error("Error: %s, in SubHandler status_change_notification", error)

    def event_notification(self, event):
        try:
            self.connector.logger.debug("Python: New event %s", event)
        except Exception as error:
            self.connector.error = str(self.__class__) + ": " + str(error)


if __name__ == '__main__':
    connector = OPCUAConnector()


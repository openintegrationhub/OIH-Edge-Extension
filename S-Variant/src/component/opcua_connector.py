# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 13:59:20 2020
OPCUAConnector of the OIH Edge
"""

__author__ = "TMO"

# {
#   „name“: „connector“,
#   „config“: {
#   	„url“: „url“,
#   	„security“: {
#   		Either as user:
# 		    „username“: „user“,
# 		    „password“: „pw“
# 		    Or as anonymous user:
# 		    "username": "" # leave these fields blank or don't use them for
# 		                   # anonymous login
#           "password": ""
# 		    And (Optional):
#           "ca_cert": "" # you must not specify a ca_cert
# 		    “policy”: “”,
# 		    “certificate”: “”,
# 		    “mode”: “”,
# 		    “private_key”: “”
#           "private_key_password": ""
#   	},
#   	“time_out”: 2000,
#       "device_id": ""
#       "mode": {
#           "mode": "pol"/"sub",
#           "discovery": "True"/"False",
#           "node_ids": ["", ""], # Je nach Mode kann man entweder die NodeId
#                                # eines Sensors angeben oder eine Vater Node
#                                # von denen man die Kinder Nodes subscriben/
#                                # pollen will. discPol/discSub: Für RootNode
#                                # leer lassen
#           "type": ["", ""] #Default: "BaseDataVariableType",
#           "to_ignore": ["Views", "Types", "Server"], # Folders and
#                                                      # Objects to
#                                                     # be Ignored while
#                                                     # browsing through the
#                                                     # Address Space
#           "sub_check_time"/"pol_time": 100/5 # Je nach Modus: "discPol" und
#                                            # subCheckTime in Mili für "sub"/
#                                            #"discSub"/pol_time in Sek für
#                                            #"pol"
#       }
#   }
# }
from concurrent.futures import TimeoutError as FuturesTimeoutError

import asyncio
import datetime
import logging

import asyncua
from asyncua import ua, Client

from component.connector_base_class import ConnectorBaseClass


class Connector(ConnectorBaseClass):
    """This class is used to connect an asyncua client to an OPCUA-Server.
    Furthermore, it is used to read data from nodes either via subscription
    or data polling and write their values into a buffer.

    Attributes:
    -----------
        config (dict): Given configuration.

        error (str): Stores error messages, which will be written into the
        error logs.

        info (str): Stores info messages, which will be written into the
        terminal.

        logger (logger): Its usage is to write debug and error logs.

        host (str): In the config specified host to connect to.

        device_id (str): TO-IGNORE

        time_out (int): Each request sent to the server expects an answer
        within this time. The timeout is specified in seconds.

        node_ids (list): List of node_ids of the opcua server.

        pol_time (int): Time intervals at which data is polled of the opcua
        server. pol_time in Sec

        type (str): Its usage is to filter nodes of the same type.

        sub_check_time (int): Time interval at which the subscription checks
        for data change.

        args (str): To-Ignore, its usage was supposed to be the arguments of
        function of the opcua server.

        to_ignore (list): List of node_ids to ignore.

        statistics (dict): Its usage is to stores the number of messages
        received from the opcua server and the messages sent to the buffer.

        data (dict): Its usage is used to store the data before it is written
        into the buffer.

        dict (dict): Its usage is to store every node and its corresponding
        father node.

        node_counter (int): Its usage is to count the discovered nodes.

        interest_nodes (list): Stores a list of nodes, which were discovered
        by the discovery method.

        subscribed (bool): True if subscription is created.

        connected (bool): True if the opcua client is connected to the opcua
        server.

        client (asyncua.Client): Client object whichs function is to connect to
        the opcua server.

        sub (SubHandler): Its usage is to hold an Instance of the SubHandler
        whichs function is to write the incoming data change into the buffer.

        terminated (bool): Status flag of the flow, if True the flow is
        stopped.

        status (str): Status flag of the connector, either 'start' or 'stop'.

    Methods:
    --------
        run(): This method is used to call either the polling method or the
        subscription method.

        _check_connection(): This method functions as health check.

        _write(nodes: list): This method writes the value of the given
        nodes in the specified time intervals(pol_time) into the buffer.

        _is_list(node: asyncua.Node, value: float): This method breaks
        down the given value to a scalar data type and then writes it into
        the buffer. This method slows down the program tremendously,
        therefore, it is currently not used.

        _connect(): This method connects the Client to the OpcUaServer.
        Either you sign in as an anonymous user or as specified user with
        username and password or with a security_string.

        query_pol(): This method calls the _connect method to establish a
        connection,
        initializes the nodes, which are either given as a list of node_ids
        or discovered by the discovery method. These nodes will be
        given to the _write method.

        query_subscription(): This method calls the _connect method to
        establish a connection and initializes the nodes, which are either
        given as a list of node_ids or discovered by the discovery method.
        These nodes will be given to the _subscribe method.

        _subscribe(): This method is used to create a subscription and to
        subscribe to a given set of nodes.

        _discovery(root_node: asyncua.Node): This methods usage is to iterate
        through the entire Server either via a given node or the RootNode
        and writes the current node, its type definition, its datatype, its
        NodeClass and its parent node_id into the debug file.

        _browse(root_node: asyncua.Node): This methods usage is to discover
        nodes with the same DataType as specified in the config.

        _methods(): TO-IGNORE
    """

    def __init__(self, config: dict, buffer):
        """Provide configuration as dict. Use errors and info array to save
        messages.

        Parameters:
        -----------
            config (dict): User configuration.

            buffer (Buffer): Buffer instance in which the data of the
            connector will be stored.
        """
        super().__init__(config, buffer)
        self.logger = logging.getLogger()
        self.config = config
        self.host = config['url']
        # self.device_id = config['device_id']
        self.time_out = config['time_out']
        self.node_ids = config['node_ids']
        if "pol" == config['mode']['mode']:
            self.pol_time = config['mode']['pol_time']
            if "True" == config['mode']['discovery']:
                if "type" in config['mode']:
                    self.type = config['mode']['type']
                else:
                    self.type = "BaseDataVariableType"
        elif "sub" == config['mode']['mode']:
            self.sub_check_time = config['mode']['sub_check_time']
            if "type" in config['mode']:
                self.type = config['mode']['type']
            else:
                self.type = "BaseDataVariableType"
        elif "methods" == config['mode']['mode']:
            self.args = config['mode']['args']
        if "to_ignore" in config['mode']:
            self.to_ignore = config['mode']['to_ignore']
        self.buffer = buffer
        self.statistics = {"MessageReceived": 0, "MessageSent": 0}
        self.dict = {}
        self.node_counter = 0
        self.interest_nodes = []
        self.subscribed = False
        self.connected = False
        self.client = None
        self.sub = None
        self.info = None
        self.terminated = False
        self.error = None
        self.status = "stop"
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        logging.getLogger('asyncua').setLevel(logging.WARNING)
        self.start()

    def run(self):
        """This method is used to call either the polling method or the
        subscription method.
        """
        self.info = "OPCUAConnector started"
        self.logger.info("OPCUAConnector started")
        if "sub" == self.config['mode']['mode']:
            asyncio.run(self.query_subscription())
        elif "pol" == self.config['mode']['mode']:
            asyncio.run(self.query_pol())
        # elif "methods" == self.config['mode']['mode']:
        #    asyncio.run(self.methods())
        self.logger.info("OPCUAConnector stopping")
        self.info = "OPCUAConnector stopping"

    async def _check_connection(self):
        """This method functions as health check."""
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
            self.logger.error("Error: %s, in _check_connection", error)
            if self.connected:
                await self.client.disconnect()

    async def _write(self, nodes: list):
        """
        This method writes the value of the given
        nodes in the specified time intervals into the buffer.

        Parameters:
        -----------
            nodes (list): Set of asnycua.Nodes.
        """
        try:
            while not self.terminated:
                while self.status == "start":
                    time = datetime.datetime.now().timestamp()
                    # Health Check
                    await self._check_connection()
                    if not self.connected and not self.terminated:
                        await self._connect()
                    data = {
                        'metadata': {
                            'deviceID': ""
                        },
                        'data': {

                        }
                    }
                    # Poll the data of all given Nodes
                    value = await self.client.read_values(nodes)
                    timestamp = datetime.datetime.now().strftime(
                        "%Y-%m-%dT%H:%M:%S.%f")
                    # Create Node-Value-Pairs
                    pairs = dict(zip(nodes, value))
                    for pair in pairs:
                        data['metadata']['deviceID'] = str(
                            await pair.get_parent())
                        data['data'][str(pair)] = []
                        value_set = {'timestamp': timestamp,
                                     'value': float(pairs[pair])}
                        data['data'][str(pair)].append(value_set)
                    self.buffer.fill_buffer(data)
                    time = datetime.datetime.now().timestamp() - time
                    await asyncio.sleep(float(self.pol_time) - time)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _write", error)
            if self.connected:
                await self.client.disconnect()

    async def is_list(self, data: dict, node: asyncua.Node, value: float):
        """This method breaks down the given value to a scalar data type
        and then writes it into the buffer. This method slows down the
        program tremendously, therefore, it is currently not used.

        Parameters:
        -----------
            node (asyncua.Node): Given node of the value.

            value (float): Value to break down to a scalar data type.
        """
        if isinstance(value, list):
            for val in value:
                await self.is_list((node + " " + str(value.index(val))), val)
        else:
            data['data'][node] = []
            value_set = {'timestamp':
                             datetime.datetime.now()
                                 .strftime("%Y-%m-%dT%H:%M:%S.%f"),
                         'value': float(value)}
            data['data'][node].append(value_set)
            self.buffer.fill_buffer(data)

    async def _connect(self):
        """This method connects the Client to the OpcUaServer.
        Either you sign in as an anonymous user or as specified user with
        username and password or with a security_string.
        """
        try:
            self.client = Client(self.host, self.time_out)
            if "policy" in self.config['security']:
                security_string = self.config['security']['policy'] \
                                  + "," + self.config[
                                      'security']['mode'] \
                                  + "," + self.config[
                                      'security']['certificate'] \
                                  + "," + self.config[
                                      'security']['private_key'] \
                                  + "::" + self.config[
                                      'security']['private_key_password']
                if "ca_cert" in self.config['security']:
                    security_string = security_string + "," + self.config[
                        'security']['ca_cert']
                await self.client.set_security_string(security_string)
                await self.client.connect()
                self.logger.debug("Logged in with security String.")
            if "username" in self.config['security']:
                self.client.set_user(self.config['security']['username'])
                self.client.set_password(self.config['security']['password'])
                await self.client.connect()
                self.logger.debug("Logged in as user %s.",
                                  self.config['security']['username'])
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
        """This method calls the _connect method to establish a connection and
        initializes the nodes, which are either given as a list of node_ids
        or discovered by the discovery method. These nodes will be
        given to the _write method.

        Exceptions:
        -----------
            This method raises a RuntimeException if there are no
            node_ids given in the config, when not using the discovery.
        """
        try:
            # Establish Connection
            await self._connect()
            if self.config['mode']['discovery'] == "False":
                if self.node_ids:
                    # Append all Nodes given via the config into a list
                    nodes = []
                    for node_id in self.node_ids:
                        nodes.append(self.client.get_node(node_id))
                    await self._write(nodes)
                else:
                    # Raise a RuntimeError, if no Nodes are given in the Config
                    raise RuntimeError
            elif self.config['mode']['discovery'] == "True":
                # If there are Nodeids given in the Config, call the _browse
                # method with the given Node, otherwise use the rootNode
                if self.node_ids:
                    for node_id in self.node_ids:
                        await self._browse(self.client.get_node(node_id))
                else:
                    await self._browse(self.client.get_root_node())
                self.logger.debug("NodeCount: %s", self.node_counter)
                await self._write(self.interest_nodes)
            if self.terminated and self.connected:
                await self.client.disconnect()
        except RuntimeError as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error(
                "Error: No NodeIds given in non-discovery mode! %s", error)
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

    async def query_subscription(self):
        """This method calls the _connect method to establish a connection
        and initializes the nodes, which are either given as a list of node_ids
        or discovered by the discovery method. These nodes will be given to
        the _subscribe method.

        Exception:
        -----------
            This method raises a RuntimeException if there are no
            node_ids given in the config, when not using the discovery.
        """
        try:
            # Establish connection
            await self._connect()
            while not self.terminated:
                if self.config['mode']['discovery'] == "False":
                    if self.node_ids:
                        # Append all Nodes given via the config into a list
                        if not self.subscribed and self.connected and \
                                not self.interest_nodes:
                            for nodeid in self.node_ids:
                                self.interest_nodes.append(
                                    self.client.get_node(nodeid))
                                # Write the ParentNodeId in a seperate
                                # dict to ensure that the data has the
                                # right metadata tag
                                self.dict[self.client.get_node(nodeid)] = \
                                    await self.client.get_node(nodeid) \
                                        .get_parent()
                    else:
                        # Raise a RuntimeError, if no Nodes are given in the
                        # Config
                        raise RuntimeError
                elif "True" == self.config['mode']['discovery']:
                    if not self.interest_nodes and self.connected:
                        # If there are Nodeids given in the Config, call
                        # the _browse method with the given Node, otherwise
                        # use the rootNode
                        if self.node_ids:
                            for nodeid in self.node_ids:
                                await self._browse(
                                    self.client.get_node(nodeid))
                        else:
                            await self._browse(self.client.get_root_node())
                        self.logger.debug("NodeCount: %s", self.node_counter)
                while self.status == "start":
                    # Health Check
                    await self._check_connection()
                    if not self.connected and not self.terminated:
                        await self._connect()
                    # Create Subscription
                    if not self.subscribed:
                        await self._subscribe(self.interest_nodes)
                    # Keeps the Thread alive
                    if self.connected and self.subscribed:
                        await asyncio.sleep(1)
                # Make sure the program gets properly terminated
                if self.terminated:
                    if self.connected:
                        await self.client.disconnect()
        except RuntimeError as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: No NodeIds given, in non-discovery mode!"
                              " %s", error)
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

    async def _subscribe(self, nodes: list):
        """This method is used to create a subscription and to subscribe to a
        given set of nodes.

        Parameters:
        -----------
            nodes (list): Set of asyncua.Node.
        """
        try:
            if not self.subscribed and self.connected:
                if self.sub is None:
                    self.sub = await self.client.create_subscription(
                        period=self.sub_check_time, handler=SubHandler(self))
                await self.sub.subscribe_data_change(nodes)
                # self.logger.debug("Added subscription to node %s", node)
                self.subscribed = True
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _subscribe", error)
            if self.connected:
                await self.client.disconnect()

    async def _discovery(self, root_node: asyncua.Node):
        """This methods usage is to iterate through the entire
        Server either via a given node or the RootNode and writes
        the current node, its type definition, its datatype, its
        NodeClass and its parent node_id into the debug file.

        Parameters:
        -----------
            root_node (asyncua.Node): node of the opcua server.
        """
        try:
            if not self.terminated and self.connected:
                children = await root_node.get_children()
                if root_node == self.client.get_root_node():
                    self.logger.debug("RootNode: %s", root_node)
                    for node in children:
                        browse = await node.read_display_name()
                        self.logger.debug("DefaultNode: %s, Name: %s", node,
                                          browse.Text)
                        await self._discovery(node)
                else:
                    for node in children:
                        node_class = await node.read_node_class()
                        parent = await node.get_parent()
                        browse = await node.read_display_name()
                        reflist = await node.get_references(
                            direction=ua.BrowseDirection.Forward)
                        attr = await node.read_attributes(
                            [ua.AttributeIds.DataType])
                        self.logger.debug(
                            "Node: %s, NodeName: %s, ParentNode: %s, "
                            "Class: %s, DataType: %s, DataDataType: %s", node,
                            browse.Text, parent, node_class,
                            reflist[0].BrowseName.Name,
                            attr[0].Value.Value.Identifier)
                        await self._discovery(node)
        except Exception as err:
            self.error = str(self.__class__) + ": " + str(err)
            self.logger.error("Node: %s", root_node)
            self.logger.error("Error: %s, in discovery", err)
            if self.connected:
                await self.client.disconnect

    async def _browse(self, root_node: asyncua.Node):
        """This methods usage is to discover nodes with the same DataType as
        specified in the config.

        Parameters:
        -----------
            root_node (asyncua.Node): node of the opcua server.
        """
        try:
            if not self.terminated and self.connected:
                browse = await root_node.read_display_name()
                node_class = await root_node.read_node_class()
                children = await root_node.get_children()
                reflist = await root_node.get_references(
                    direction=ua.BrowseDirection.Forward)
                if root_node == self.client.get_root_node():
                    for node in children:
                        await self._browse(node)
                elif ua.NodeClass.Variable == node_class:
                    if any(reflist[0].BrowseName.Name == dType
                           for dType in self.type):
                        attr = await root_node.read_attributes(
                            [ua.AttributeIds.DataType])
                        # self.logger.debug("Hier %s",
                        # attr[0].Value.Value.Identifier)
                        if 0 < attr[0].Value.Value.Identifier < 12:
                            if await root_node.get_user_access_level() \
                                    >= await root_node.get_access_level():
                                self.interest_nodes.append(root_node)
                                self.dict[root_node] = \
                                    await root_node.get_parent()
                                # self.logger.debug("%s appended", browse.Text)
                                self.node_counter += 1
                    for node in children:
                        await self._browse(node)
                elif reflist[0].BrowseName.Name == "FolderType":
                    if any(browse.Text == name for name in self.to_ignore):
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
                    if any(browse.Text == name for name in self.to_ignore):
                        return
                    if "Server" == browse.Text:
                        return
                    for node in children:
                        await self._browse(node)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Node: %s", root_node)
            self.logger.error("Error: %s, in browse", error)
            if self.connected:
                await self.client.disconnect()

    # This code fragment is not yet finished.
    async def methods(self):
        """TO-IGNORE"""
        try:
            while not self.terminated and not self.connected:
                await self._connect()
            while not self.terminated:
                while self.status == "start":
                    data = {
                        'metadata': {
                            'deviceID': ""
                        },
                        'data': {

                        }
                    }
                    for node_id in self.node_ids:
                        node = self.client.get_node(node_id)
                        value = await node.call_method(node_id, *self.args)
                        data['data'][str(node)] = []
                        value_set = {'timestamp': datetime.datetime.now()
                            .strftime("%Y-%m-%dT%H:%M:%S.%f"),
                                     'value': float(value)}
                        data['data'][str(node)].append(value_set)
                        self.buffer.fillBuffer(data)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.error("Error: %s, in _write", error)
            if self.connected:
                await self.client.disconnect()


class SubHandler:
    """This class handles the subscribed nodes.

    Attributes:
    -----------
        connector (connector): Instance of the opcua connector.

    Methods:
    --------
        datachange_notification(node: asyncua.Node, val: float,
        data: asyncua.common.subscription.DataChangeNotif): This method
        handles the data change events of the subscribed nodes, it passes the
        nodes and the value to a method, which writes the data into the
        buffer.

        is_list(node: asnycua.Node, value: float, timestamp: datetime): This
        method writes the value of the node into the buffer if it is a
        scalar data type. If it is a list it iterates through the given
        value and calls this method again.

        status_change_notification(event): This method handles status changes.

        event_notification(event): This method handles events.
    """

    def __init__(self, connector):
        self.connector = connector

    def datachange_notification(self,
                                node: asyncua.Node,
                                val: float,
                                data: asyncua.common
                                    .subscription.DataChangeNotif):
        """This method handles the data change events of the subscribed
        nodes, it passes the nodes and the value to a method, which writes
        the data into the buffer.

        Parameters:
        -----------
            node (asnycua.Node): Node from which the data has changed

            val (float): Value of the given node.

            data (DataChangeNotif): DataChangeNotification object.
        """
        try:
            self.connector.logger.debug("Python: New data change event on node"
                                        " %s, with val: %s and data %s",
                                        node, val, str(data))
            # self.connector.messageCounter += 1
            # self.connector.logger.debug("Connector Message Counter %s",
            # self.connector.messageCounter)
            # Call the isList method to write the data into the buffer
            self.is_list(node, val, data.monitored_item.Value.SourceTimestamp)
            # self.connector.data_to_send.append([node, val])
        except Exception as error:
            self.connector.error = str(self.__class__) + ": " + str(error)
            self.connector.logger.error("Error: %s, in SubHandler "
                                        "datachange_notification", error)

    def is_list(self, node: asyncua.Node,
                value: float,
                timestamp: datetime):
        """This method writes the value of the node into the buffer if it
        is a scalar data type. If it is a list it iterates through the given
        value and calls this method again.

        Parameters:
        -----------
            node (asnycua.Node): Node from which the data has changed.

            value (float): Value of the given node, which will either be a
            list or a scalar value.

            timestamp (datetime): Timestamp of the data change.
        """
        if isinstance(value, list):
            # If a list is given, break the List down to a scalar value,
            # otherwise, fill the buffer with the given value
            for val in value:
                self.is_list((node + " " + str(value.index(val))), val,
                             timestamp)
        else:
            data = {
                'metadata': {
                    'deviceID': ""
                },
                'data': {

                }
            }
            data['metadata']['deviceID'] = str(
                self.connector.dict[node])
            data['data'][str(node)] = []
            value_set = {'timestamp':
                             timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                         'value':
                             float(value)}
            data['data'][str(node)].append(value_set)
            self.connector.buffer.fill_buffer(data)

    def status_change_notification(self, event):
        """This method handles status changes."""
        try:
            self.connector.logger.debug("Python: New Status event change %s",
                                        event)
        except Exception as error:
            self.connector.error = str(self.__class__) + ": " + str(error)
            self.connector.logger.error("Error: %s, in SubHandler "
                                        "status_change_notification", error)

    def event_notification(self, event):
        """This method handles events."""
        try:
            self.connector.logger.debug("Python: New event %s", event)
        except Exception as error:
            self.connector.error = str(self.__class__) + ": " + str(error)

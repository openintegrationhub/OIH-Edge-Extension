import datetime
import json
import time
from json import JSONDecodeError
from numbers import Number
from typing import Union

from component_base_class.component_base_class import ComponentBaseClass
from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.register_read_message import ReadInputRegistersResponse


class ModbusConnector(ComponentBaseClass):
    def __init__(self):
        """ Constructor of the Modbus Connector. """
        try:
            super().__init__()
        except Exception as error:
            print(f'Failure in Base Class, {error}')
        config_template = {
            "name": "",
            "kafka_broker": "",
            "slaves": "",
            "timeout_attempts": 0
        }

        # LOGGER
        self.logger = self.get_logger()

        # CONFIG
        self.config = {}
        self.unsend = 0
        self.producer = None
        self.connected = False
        self._client = None
        self.load_config(config_template)

        if not self.terminated:
            self.start()

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
            config = self.get_config(
                config_template,
                source=source,
                file_path=f'/config/{self.path_name}'
            )
        else:
            config = self.wait_for_config_insertion()
        self.config = config
        try:
            if self.config and all(keys in self.config
                                   for keys in config_template):
                if "kafka_broker" in config:
                    self.producer = KafkaProducer(
                        bootstrap_servers=[config["kafka_broker"]])
            else:
                self.logger.error('Missing key(s) in config')
                print('Missing key(s) in config', flush=True)
                self.terminated = True
                return
        except Exception as error:
            self.logger.error(f'Error: {error} in load_config')
            self.terminated = True

    @staticmethod
    def read_registers(client: ModbusClient, slave: dict) \
            -> Union[ReadInputRegistersResponse, ReadHoldingRegistersResponse]:
        """ Read slave config and return the read register method.

        :param client: Modbus Client
        :param slave: Slave of the modbus server
        :return:
        """
        start_address = slave["start_address"]
        count = slave["count"]
        unit = slave["unit"]
        method = slave["method"]

        return {
            "read_input": client.read_input_registers(
                address=start_address,
                count=count,
                unit=unit
            ),
            "read_holding": client.read_holding_registers(
                address=start_address,
                count=count,
                unit=unit
            )
        }[method]

    @staticmethod
    def format_data(topic: str, value: Union[int, Number]) -> dict:
        """ Format the given data into our specific data model.

        :param topic: Field and topic name
        :param value: Given value
        :return: (dict) formatted data
        """
        data = {
            'metadata': {
            },
            'data': {
            }
        }
        data["data"][topic] = []
        data["data"][topic].append(
            {
                'timestamp': datetime.datetime.now().strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"),
                "value": value
            })
        return data

    def on_broker_delivery(self, original_message):
        """ Callback of the kafka broker, if the message is successfully sent.

        :param original_message: message to be sent.
        :return: None
        """
        self.logger.debug(
            "Kafka broker received message: " + str(original_message))

    def start(self):
        """ Main function of the modbus producer.

        :return: None
        """
        try:
            while not self.terminated:
                self.connected = True
                # Create a client for each slave.
                slaves = self.config["slaves"]
                for slave in slaves:

                    host = slave["host"]
                    port = slave["port"]
                    topic = slave["topic"]
                    unit = slave["unit"]

                    self._client = ModbusClient(host, port)

                    if self._client.connect():
                        result = self.read_registers(self._client, slave)
                        print(result, flush=True)

                        if not hasattr(result, "registers"):
                            break

                        for register in result.registers:
                            # Send data
                            formatted_data = self.format_data(topic, register)
                            try:
                                self.producer.send(
                                    topic,
                                    value=json.dumps(formatted_data).encode(
                                        'utf-8'),
                                    key=json.dumps(unit).encode('utf-8')) \
                                    .add_callback(self.on_broker_delivery)
                                self.producer.flush()
                            except KafkaTimeoutError as timeout_err:
                                self.logger.error(f'Kafka broker timeout, '
                                                  f'{timeout_err}')
                            except JSONDecodeError as decode_err:
                                self.unsend += 1
                                self.logger.warning(f'Could not decode '
                                                    f'message.'
                                                    f'Unsend: {self.unsend}')
                                self.logger.error(decode_err)
                time.sleep(2)
        except Exception as error:
            self.logger.error(f'Error: {error} in start')
        finally:
            self._client.close()


if __name__ == '__main__':
    modbus_producer = ModbusConnector()

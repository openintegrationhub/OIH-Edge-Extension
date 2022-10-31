from kafka.errors import KafkaError
from kafka import KafkaProducer
from logging import handlers
import threading
import logging
import secrets
import signal
import queue
import json
import ast
import sys
import os


class ComponentBaseClass:
    """
    Base class for Kafka components that implements different logging handlers, configuration methods and system signal
    listener for gracefully shutting down the component.
    """
    signals = {
        signal.SIGINT: 'SIGINT',
        signal.SIGTERM: 'SIGTERM',
        signal.SIGILL: 'SIGKILL'
    }

    def __init__(self):
        """
        Constructor method of ComponentBaseClass
        """
        self.__logger = logging.getLogger()
        self.__config = None
        self.__kafka_broker = None
        self.__kafka_handler = None
        self.__error_handler = None
        self.__debug_handler = None
        self.__producer = None
        self.terminated = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGILL, self.exit_gracefully)

    @staticmethod
    def str_convert(exp: str) -> any:
        """
        Converts string representations of dictionaries or lists to their original type.

        :param exp: (str) expression to be converted
        :return: (any) returns a dict or list object if 'exp' was a string representation of a dictionary or list.
            Otherwise the original string is returned.
        """
        if len(exp) > 1 and exp[0] in ["{", "["]:
            return ast.literal_eval(exp)
        else:
            return exp

    def exit_gracefully(self, signum: signal.Signals, frame: any):
        """
        Listens for system signals and sets 'self.terminated' to True when application is canceled in order to
        gracefully stop any processing loops.

        :param signum: (signal) system signal received from docker environment
        :param frame: (any) current frame in process
        :return: None
        """
        # use 'self.terminated = False' as condition for processing loops
        self.terminated = True
        print(f"Received {self.signals[signum]}")
        for handler in self.__logger.handlers:
            logging.Handler.close(handler)
        print("Cleaning up resources. Shutting down container...")
        sys.stdout.flush()

    def get_config(self, config: dict, source="env", file_path="/config", ) -> dict:
        """
        Returns configuration from environment variables or configuration file.

        :param config: (dict) dict with required configuration keys. Keys found in environment variables are filled up
            with their respective values, missing keys get NULL value. Dict can be completely empty when using
            "file"-method.
        :param source: (str, optional) reads configuration from environment variables when set to "env" or from config
            file when set to "file". Defaults to "env".
        :param file_path: (str, optional) folder in which to search for config.json file. Defaults to "/config".
        :return: (dict) dictionary with configuration found in environment variables or configuration file.
        """
        if source == "env":
            # get config dict from environment variables and print which keys don't match
            self.__config = {config_k: self.str_convert(os.environ.get(config_k))
                             if config_k in os.environ.keys()
                             else print(f"Key '{config_k}' not found in environment variables.")
                             for config_k in config.keys()}
        elif source == "file":
            combined_path = "." + file_path
            config_file_path = os.path.join(combined_path, "config.json")
            print("config_file_path = " + str(config_file_path))
            try:
                # get config dict from file
                with open(config_file_path) as json_file:
                    file_config = json.load(json_file)
                    json_file.close()
                    self.__config = file_config
            except OSError as error:
                print(f"File {config_file_path} cannot be read. Error: {error}")
                sys.stdout.flush()
        sys.stdout.flush()
        return self.__config

    def get_logger(self, logger_type="file", file_path="/logs", max_log_files=0, kafka_config=dict) -> logging.Logger:
        """
        Returns the standard logger with file- or Kafka-handler. Can also be called more than one time to combine
        both logging methods.

        :param logger_type: (str, optional) "file" for file logger, "kafka" for kafka logger. Defaults to "file".
        :param file_path: (str, optional) relative file path to log files. Defaults to "./logs".
        :param max_log_files: (int, optional) maximum number between 1 and 9 of backup log files used by logger.
            Defaults to 1.
        :param kafka_config: (dict, mandatory when "logger_type" is set to "kafka") Kafka configuration in form of dict
            like {"bootstrap_servers": "localhost:9092", "topic": "Kafka-Logging", "key": "Component X"
            [, debug: True/False (optional)]}.
            If value of "key" is left empty ("key": ""), a random key like "Kafka-Logger#aj3hxd8s" is created
            automatically. If a "debug" key is present and set to True, all internal Kafka messages will be logged too.
            Use with caution! Kafka produces hundreds to thousands of messages per minute.
        :return: Logger
        """
        # LOGGING-FORMATTER
        __logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %('
                                                'message)s')

        if logger_type == "file":
            try:
                relative_path = "." + file_path
                # Create logging directory if it doesn't already exist
                try:
                    os.makedirs(relative_path, exist_ok=True)
                    print(f"Directory {relative_path} created successfully")
                except OSError as error:
                    print(f"Directory {relative_path} can not be created. Error: {error}")
                    sys.stdout.flush()

                __max_log_files = 9 if max_log_files > 9 else (1 if max_log_files < 1 else max_log_files)
                # ERROR-HANDLER
                self.__error_handler = logging.handlers.RotatingFileHandler(os.path.join(relative_path, "error.log"),
                                                                            maxBytes=1024 * 1024 * 2,
                                                                            backupCount=__max_log_files,
                                                                            delay=False)
                self.__error_handler.setLevel(logging.WARNING)
                self.__error_handler.setFormatter(__logging_formatter)
                # DEBUG-HANDLER
                self.__debug_handler = logging.handlers.RotatingFileHandler(os.path.join(relative_path, "debug.log"),
                                                                            maxBytes=1024 * 1024 * 2,
                                                                            backupCount=__max_log_files,
                                                                            delay=False)
                self.__debug_handler.setLevel(logging.DEBUG)
                self.__debug_handler.setFormatter(__logging_formatter)
                # LOGGER
                self.__logger.setLevel(logging.DEBUG)
                self.__logger.addHandler(self.__error_handler)
                self.__logger.addHandler(self.__debug_handler)
                sys.stdout.flush()
            except Exception as error:
                print(f"Kafka-Logger error: {error}")
                sys.stdout.flush()
        elif logger_type == "kafka":
            try:
                config = {"bootstrap_servers": "", "topic": "", "key": ""}
                if kafka_config is not None and all(key in kafka_config for key in config):
                    # KAFKA-HANDLER
                    self.__kafka_handler = self.__KafkaLoggingHandler(
                        bootstrap_servers=str(kafka_config["bootstrap_servers"]),
                        topic=str(kafka_config["topic"]),
                        key=str(kafka_config["key"]),
                        debug=True if "debug" in config and config["debug"] is True else False)
                    self.__kafka_handler.setLevel(logging.DEBUG)
                    self.__kafka_handler.setFormatter(__logging_formatter)
                    # LOGGER
                    self.__logger.setLevel(logging.DEBUG)
                    self.__logger.addHandler(self.__kafka_handler)
            except Exception as error:
                print(f"Kafka-Logger error: {error}")
                sys.stdout.flush()
        sys.stdout.flush()
        return self.__logger

    class __KafkaLoggingHandler(logging.StreamHandler):
        """
        LoggingHandler that writes log messages into a Kafka topic.
        """

        def __init__(self, bootstrap_servers: str, topic: str, key: str, debug: bool = False) -> None:
            """
            Constructor method of KafkaLoggingHandler.

            :param bootstrap_servers: (str) Kafka-Cluster host and port in "host:port" format.
            :param topic: (str) Kafka topic to write log messages into.
            :param key: (str) Kafka key to be used when writing messages. If key is empty, a random key like
                "Kafka-Logger#" + 8-digit hex number is created automatically.
            :param debug: (bool) Enable debugging mode. When set to 'True' internal Kafka messages are logged
                additionally. Defaults to 'False'.
            """
            super().__init__()
            try:
                self.__bootstrap_servers = bootstrap_servers
                self.__debug = debug
                self.__kafka_producer = None
                self.__kafka_producer = KafkaProducer(bootstrap_servers=self.__bootstrap_servers)
                self.__q = queue.Queue()
                self.__shutdown = False
                self.__topic = topic
                if len(key) == 0:
                    token = secrets.token_hex(4)
                    self.__key = f"Kafka-Logger#{token}"
                else:
                    self.__key = key
                threading.Thread(target=self.send_kafka_msg, daemon=True).start()
            except KafkaError as error:
                if self.__kafka_producer is None:
                    print("Kafka-Logger error: Kafka-Cluster not available.")
                    return
                print(f"Kafka-Logger error: {error}")
                sys.stdout.flush()

        def send_kafka_msg(self):
            while not self.__shutdown:
                msg = self.__q.get()
                self.__kafka_producer.send(topic=self.__topic,
                                           key=json.dumps(self.__key).encode('utf-8'),
                                           value=json.dumps(msg).encode('utf-8'))
                self.__kafka_producer.flush()
                self.__q.task_done()

        def emit(self, record: logging.LogRecord) -> None:
            """
            Emits logging message to logger.

            :param record: (LogRecord) record to be logged.
            :return: None
            """
            # drop kafka logging to avoid infinite recursion
            try:
                msg = self.format(record)
                if record.name.find('kafka') >= 0:
                    if self.__debug:
                        print(f"Kafka-Logger info: {record}", flush=True)
                        log = True
                    else:
                        return
                elif self.__kafka_producer is None:
                    print("Kafka-Logger error: Kafka-Cluster not available.", flush=True)
                    return
                else:
                    log = True
                if log:
                    self.__q.put(msg)

            except KafkaError as error:
                print(f"Kafka-Logger error: {error}")
                sys.stdout.flush()

        def close(self):
            """
            Closes Kafka producer.

            :return: None
            """
            try:
                self.__q.join()
                self.__shutdown = True
                if self.__kafka_producer is not None:
                    self.__kafka_producer.close()
            except KafkaError as error:
                print(f"Kafka-Logger error: {error}")
                sys.stdout.flush()

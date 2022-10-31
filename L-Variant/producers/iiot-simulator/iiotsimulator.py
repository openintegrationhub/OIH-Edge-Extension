import datetime
import json
import secrets
import time

import numpy as np
import pandas as pd
from kafka import KafkaProducer

import log

# EXAMPLE CONFIG CUSTOM:{
#	"bootstrap_servers": "localhost:9092",
#	"topic" : "kafka_source_component_test",
#	"key": "kafka_source",
#	"simulator_config":
#        "type":"custom",
#        "period" : 60,
#        "interval": 1,
#        "sensors":{
#            "zk_spannung": [50,999],
#            "zk_strom": [10,240],
#            "wr_spannung": [30,555],
#            "wr_strom": [10,120]
#        }
# }
# EXAMPLE CONFIG CSV:{
#	"bootstrap_servers": "localhost:9092",
#	"topic" : "kafka_source_component_test",
#	"key": "kafka_source_csv",
#	"simulator_config":
#        "type":"csv",
#        "interval" : 60,
#        "timestamp": "auto" #default is auto, to generate a timestamp for
#        each record with the current timestamp
#        "csv_config":{}  #config as input for pandas read_csv function
# }



def custom_simulator(custom_config: dict):
    """ Generates custom simulation data, the user defines a min and max value,
    along with an interval and a period and this function generates the
    data evenly according to period/interval. This generated data will be
    sent to the specified kafka broker in the given intervals until the
    component gets shutdown.

    :param custom_config: Simulator config
    :return: None
    """
    bootstrap_servers = custom_config['bootstrap_servers']
    topic = custom_config['topic']
    kafka_key = custom_config['key']
    if kafka_key == "":
        generate_key = True
    else:
        generate_key = False
    simulator_config = custom_config['simulator_config']
    period = simulator_config['period']
    interval = simulator_config['interval']
    sensors = simulator_config['sensors']
    sensor_values = {}
    size = int(period / interval)
    for sensor in sensors:
        sensor_values[sensor] = np.geomspace(
            sensors[sensor][0],
            sensors[sensor][1],
            size)
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
    log.logging.info('Connected to Kafka Broker')
    count = 0
    while True:
        # Check for key
        if generate_key:
            record_key = secrets.token_hex(4).encode('utf-8')
        else:
            record_key = kafka_key.encode('utf-8')
        for value_index in range(size):
            time.sleep(interval)
            t_now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            new_message = {
                "data": {},
                "metadata": {}}
            for sensor in sensor_values:
                new_message['data'][sensor] = [{
                    "value": sensor_values[sensor][value_index],
                    "timestamp": t_now}]

            log.logging.info('new_message', new_message)
            record_value = json.dumps(new_message).encode('utf-8')
            producer.send(topic, key=record_key, value=record_value)
            count += 1
        log.logging.info(
            f'we\'ve sent {count} messages to {bootstrap_servers}')
        producer.flush()


def csv_simulator(csv_config: dict):
    """ Read data from a csv file and send it to a kafka broker.

    :param csv_config: Simulator config
    :return: None
    """
    bootstrap_servers = csv_config['bootstrap_servers']
    topic = csv_config['topic']
    kafka_key = csv_config['key']
    if not kafka_key:
        generate_key = True
    else:
        record_key = kafka_key.encode('utf-8')
    producer = KafkaProducer(bootstrap_servers=[bootstrap_servers])
    log.logging.info('Connected to Kafka Broker')
    simulator_config = csv_config['simulator_config']
    simulator_config['csv_config']['filepath_or_buffer'] = r"./data/data.csv"
    interval = simulator_config['interval']
    data_frame = pd.read_csv(**simulator_config['csv_config'])
    count = 0
    for _, row in data_frame.iterrows():
        time.sleep(interval)
        t_now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        new_message = {
            "data": {},
            "metadata": {}}
        for i, value in enumerate(row):
            if generate_key and i == 0:
                record_key = str(value).encode('utf-8')
                continue
            if simulator_config['timestamp'] == 'auto':
                new_message['data'][row.keys()[i]] = [{
                    "value": value,
                    "timestamp": t_now}]
            else:
                new_message['data'][row.keys()[i]] = [{
                    "value": value,
                    "timestamp": row[simulator_config['timestamp']]}]
        log.logging.info('new_message', new_message)
        record_value = json.dumps(new_message).encode('utf-8')
        producer.send(topic, key=record_key, value=record_value)
        count += 1
    log.logging.info(
        f'we\'ve sent {count} messages to {bootstrap_servers}')
    producer.flush()


if __name__ == "__main__":
    log.logging.info('Load and read configuration')
    MODE_PATH = r"./configs/config.json"
    with open(MODE_PATH, encoding='UTF-8') as json_file:
        config = json.load(json_file)
        json_file.close()
    if config["simulator_config"]["type"] == "csv":
        log.logging.info('Start csv simulator')
        csv_simulator(config)
    elif config["simulator_config"]["type"] == "custom":
        log.logging.info('Start custom simulator')
        custom_simulator(config)
    else:
        log.logging.error('Simulator configuration type is unknown')

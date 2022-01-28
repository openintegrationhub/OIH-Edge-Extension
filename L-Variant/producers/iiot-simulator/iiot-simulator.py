from kafka import KafkaProducer
import json
import time
import datetime
import numpy as np
import log

"""
config:{
	"bootstrap_servers":"",
	"topic" : "iiotsimdata",
	"key": "iiotsim",
	"period" : 60,
	"interval": 1,
		"sensors":{
			"zk_spannung": [50,999],
			"zk_strom": [10,240],
			"wr_spannung": [30,555],
			"wr_strom": [10,120]
		}
		}
"""

def ematec_simulator():
    mode_path = r"./configs/config.json"
    with open(mode_path) as json_file:
        config = json.load(json_file)
        json_file.close()
    bootstrap_servers = config['bootstrap_servers']
    topic = config['topic']
    kafka_key = config['key']
    period = config['period']
    interval = config['interval']
    sensors = config['sensors']
    sensor_values={}
    size=int(period / interval) + 1
    for sensor in sensors:
        sensor_values[sensor]=np.geomspace(sensors[sensor][0], sensors[sensor][1], size)
    p = KafkaProducer(bootstrap_servers=bootstrap_servers)
    log.logging.info('Connected to Kafka Broker')
    count = 0
    while True:
        for value_index in range(size):
            time.sleep(interval)
            t_now=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            new_message = {
                "data": {},
                "metadata": {}}
            for sensor in sensor_values:
                new_message['data'][sensor]= [{
                        "value": sensor_values[sensor][value_index],
                        "timestamp": t_now}]
                        
            log.logging.info('new_message',new_message)
            record_key = kafka_key.encode('utf-8')
            record_value = json.dumps(new_message).encode('utf-8')
            p.send(topic, key=record_key, value=record_value)
            count+=1
        log.logging.info('we\'ve sent {count} messages to {brokers}'.format(count=count, brokers=bootstrap_servers))
        p.flush()

if __name__ == "__main__":
    log.logging.info('Start Ematec Simulator')
    ematec_simulator()
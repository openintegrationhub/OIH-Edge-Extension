import datetime
import logging


class Converter:
    def __init__(self, config):
        self.config = config
        self.config_topic = None
        #### LOGGING#####
        self.logger = logging.getLogger()

    def convert(self, content, topic):
        self.logger.debug("CONTENT=" + str(content))
        self.logger.debug("TOPIC=" + str(topic))
        topic_mapping = [topic_iter for i, topic_iter in enumerate(self.config) if topic_iter['topicName'] == topic]
        #self.logger.debug("TOPIC-MAPPING=" + str(topic_mapping))
        if topic_mapping:
            self.config_topic = topic_mapping[0]["converter"]
            if self.config_topic['type'] == "linemetrics":
                data = {
                    'metadata': {
                    },
                    'data': {
                    }
                }
                try:
                    if len(self.config_topic['filter']) > 0 and 'body' in content:
                        if 'dataProviderID' in content['body'] and content['body']['dataProviderId'] not in self.config_topic['filter']:
                            self.logger.debug("Filter > 0 but content['body']['dataProviderId'] not in self.config_topic['filter']")
                            self.logger.info("Provider not in Filter")
                            return None
                        elif 'id' in content['body'] and content['body']['id'] not in self.config_topic['filter'][content['body']['dataProviderId']]['dataStreams']:
                            self.logger.debug("Filter > 0 but not in self.config_topic['filter'][content['body']['dataProviderId']]['dataStreams']")
                            self.logger.info("DataStream not in Filter")
                            return None
                        elif 'dataProviderId' not in content['body'] or 'id' not in content['body']:
                            self.logger.debug("Unexpected message format: " + str(content['body']))
                            self.logger.info("Content['body'].keys()=" + str(content['body'].keys()))
                        else:
                            device_name = self.config_topic['filter'][content['body']['dataProviderId']]
                            data['metadata'][device_name['title']] \
                                = {"id": content["body"]["dataProviderId"],
                                   "location": device_name["location"],
                                   "dataStreams": {
                                       device_name["dataStreams"][content["body"]["id"]]["title"]: {
                                        "id": content["body"]["id"],
                                        "measurement": device_name["dataStreams"][content["body"]["id"]]["measurement"]
                                                         }
                                                 }
                                   }
                            data['data'][device_name["dataStreams"][content["body"]["id"]]["title"]] = [
                                {'timestamp': datetime.datetime.fromtimestamp(content['body']['timestamp']
                                                                              / 1000).strftime("%Y-%m-%dT%H:%M:%S"),
                                 'value': content['body']['value']['val']}]
                            self.logger.debug("MQTT-Converter-Data: " + str(data))
                            return data
                    else:
                        self.logger.error("No filter found in config!")
                        return None
                except Exception as error:
                    self.logger.exception("ERROR:")
            else:
                return None

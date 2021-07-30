import datetime


class Converter:

    @staticmethod
    def convert(config,content):
        data = {'metadata': {},
                'data': {}}

        if config['type'] == "linemetrics":

            if len(config['filter']['dataProviderId']) > 0 and content['body']['dataProviderId'] not in config['filter']['dataProviderId']:
                #print('Dataprovider',{content["body"]["dataProviderId"]},'not in filter')
                return None
            elif len(config['filter']['dataStreams']) > 0 and content['body']['id'] not in config['filter']['dataStreams']:
                #print('Datastream',{content["body"]["id"]},'not in filter')
                return None
            else:
                if content["body"]["id"] not in config["nameMapping"].keys():
                    sensor_name=content["body"]["id"]
                else:
                    sensor_name=config['nameMapping'][content["body"]["id"]]

                if content["body"]["dataProviderId"] not in config["nameMapping"].keys():
                    device_name=content["body"]["dataProviderId"]
                else:
                    device_name=config['nameMapping'][content["body"]["dataProviderId"]]

                data['data'][sensor_name]=[{'timestamp': datetime.datetime.fromtimestamp(content['body']['timestamp']/1000).strftime("%Y-%m-%dT%H:%M:%S"),
                                            'value': content['body']['value']['val']}]
                data['metadata']["deviceID"]=device_name
                return data





from threading import Lock
from component.ComponentBaseClass import ComponentBaseClass


class Buffer(ComponentBaseClass):
    def __init__(self, config):
        super().__init__(config)
        self.maxsize = config['maxsize']
        self.maxpolicy = config['maxpolicy']
        self.error = None
        self.info = None
        self.bufferempty = True
        self.bufferready = False
        self.bufferLock = Lock()
        self.buffer = {
            'metadata': {
                'deviceID': ""
            },
            'data': {
            }
        }
        if 'database' in config:
            self.database = config['database']
        if config['type'] == 'local':
            self.typechoice = 0
        elif config['type'] == 'remote':
            self.typechoice = 1
        self.procedurecall = [self.localBuffer, self.remoteBuffer]

    def fillBuffer(self, data):
        self.procedurecall[self.typechoice](data)

    def process(self, data):
        try:
            if not self.bufferready:
                return None
            else:
                with self.bufferLock:
                    self.bufferempty = True
                    self.bufferready = False
                    return self.buffer
        except (ValueError, Exception) as error:
            self.error = str(self.__class__) + ": " + str(error)
            self.logger.exception("ERROR")

    def localBuffer(self, data):
        with self.bufferLock:
            if self.bufferempty:
                self.bufferempty = False
                self.buffer['metadata'] = data['metadata']
                self.buffer['data'] = {}
                for sensor in data['data']:
                    self.buffer['data'][sensor] = []
                    for valueset in data['data'][sensor]:
                        self.buffer['data'][sensor].append(valueset)
            else:
                for device in data['metadata']:
                    if device not in self.buffer['metadata'].keys():
                        self.buffer['metadata'][device] = data['metadata'][device]
                for sensor in data['data']:
                    if sensor not in self.buffer['data'].keys():
                        self.buffer['data'][sensor] = []
                    for valueset in data['data'][sensor]:
                        self.buffer['data'][sensor].append(valueset)
            self.bufferready = True

    def remoteBuffer(self, data):
        # to be implemented in next iteration
        pass

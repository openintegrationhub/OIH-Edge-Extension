import pyaixact.server as server
from concurrent.futures import ThreadPoolExecutor
import datetime
import threading
import time


class Connector(threading.Thread):
    def __init__(self, config, buffer):
        super().__init__(name="Connector")
        self.startsubscription = threading.Event()
        self.ip = config['ip']
        self.username = config['username']
        self.password = config['password']
        self.symbols = config['symbols']
        self.buffer = buffer
        self.symbolnames = []
        self.aixactserver = None
        self.status = "stop"
        self.terminated = False
        self.error = None
        self.executor = ThreadPoolExecutor(200)
        self.threadstarted = threading.Event()
        ###############################
        self.cleaning_active = False
        self.recipe_active = False
        self.recipe_class = None
        ###############################
        self.connecttoaixact()

    # method is executed at thread start and only ends when orchestrator terminate() is called.
    # run with all symbols in one method
    def run(self):
        #self.status = "start"
        self.threadstarted.set()
        ###################TEST##################
        #self.aixactserver.on('Recipe.Class', self.recipeOut)
        #self.aixactserver.on('Recipe.Active', self.recipeOut)
        ###################TEST##################
        while not self.terminated:
            while self.status == "start":
                self.query()
        self.status = "stop"

    def recipeOut(self, path, data, timestamp):
        if type(data) is bool:
            self.recipe_active = data
        else:
            self.recipe_class = data
        print("Änderung bei Symbol: " + str(path))
        print("Neuer Status: " + "\"" + str(data) + "\"" + " bei Timestamp: " + str(timestamp) + "\n")
        if not self.cleaning_active and self.recipe_active and self.recipe_class == "Cleaning":
            print("Der Reinigungsprozess hat begonnen")
            self.cleaning_active = True
        elif self.cleaning_active and not self.recipe_active:
            print("Der Reinigungsprozess wurde beendet")
            self.cleaning_active = False

    # query with all symbols in one method
    def query(self):
        try:
            data = {
                'metadata': {
                    'deviceID': self.aixactserver.symbols['AixServer.Configuration.SystemId']
                },
                'data': {
                }
            }
            for symbol in self.symbols:
                data['data'][symbol] = []
                valueset = {'timestamp': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                            'value': self.aixactserver.symbols[symbol]}
                data['data'][symbol].append(valueset)
            self.buffer.fillBuffer(data)
        except Exception as error:
            self.error = str(self.__class__) + ": " + str(error)

    # run with one symbol per thread
    # one version with single threads and one with ThreadPoolExecutor
    '''def run(self):
        self.status = "start"
        self.threadstarted.set()
        for symbol in self.symbols:
            #name = str(symbol) + "-Thread"
            self.executor.submit(self.query, symbol)
            #symbolthread = threading.Thread(None, target=self.query, name=name, args=(symbol,))
            #symbolthread.start()
        self.startsubscription.set()
        while not self.terminated:
            time.sleep(1)
        self.status = "stop"

    # query with one symbol per thread
    def query(self, symbol):
        while not self.startsubscription.is_set():
            time.sleep(0.1)
        while self.status == "start":
            try:
                data = {
                    'metadata': {
                        'deviceID': self.aixactserver.symbols['AixServer.Configuration.SystemId']
                    },
                    'data': {
                    }
                }
                data['data'][symbol] = []
                valueset = {'timestamp': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                            'value': self.aixactserver.symbols[symbol]}
                data['data'][symbol].append(valueset)
                self.buffer.fillBuffer(data)
            except (ValueError, Exception) as error:
                self.error = str(self.__class__) + ": " + str(error)
    '''

    # run with one subscription per thread
    '''def run(self):
        self.status = "start"
        self.threadstarted.set()
        for symbol in self.symbols:
            self.aixactserver.on(symbol, self.query)
            print(f"{symbol} subscribed")
        self.startsubscription.set()
        while not self.terminated:
            self.aixactserver.wait(10)
        self.status = "stop"
        self.aixactserver.off()

    # subscribe method with one subscription per thread
    def subscription(self, symbol):
        pass

    # query with one subscription per thread
    def query(self, path, data, timestamp):
        if self.startsubscription.is_set():
            try:
                self.data = {
                    'metadata': {
                        'deviceID': self.aixactserver.symbols['AixServer.Configuration.SystemId']
                    },
                    'data': {
                    }
                }
                self.data['data'][path] = []
                valueset = {'timestamp': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                            'value': data}
                self.data['data'][path].append(valueset)
                self.buffer.fillBuffer(self.data)
            except (ValueError, Exception) as error:
                self.error = str(self.__class__) + ": " + str(error)
    '''

    # method connects to Aixact server
    def connecttoaixact(self):
        try:
            self.aixactserver = server.Aixact(self.ip, self.username, self.password)
            print('Connected to AIXACT\n')
        except (ValueError, Exception):
            self.error = "Aixact-Server not connected or wrong credentials"

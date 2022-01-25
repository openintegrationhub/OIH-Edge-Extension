from component import Aggregator_Timebased,Aggregator, Anonymizer,InfluxDBConnector, WebhookConnector
import threading
import logging


class EdgeOrchestrator(threading.Thread):
    def __init__(self, config, buffer):
        super().__init__(name="EdgeOrchestrator")
        self.flow = None
        self.data = None
        self.logger = logging.getLogger()
        self.config = config
        self.buffer = buffer
        self.status = "stop"
        self.terminated = False
        self.errors = []
        self.info = []
        self.flow_position = 0
        self.analyze_config(self.config)
        self.start()

    # Methode wird beim Erstellen des EdgeOrchestrators aufgerufen, analysiert den mode und baut den flow
    # mit den angegebenen Komponenten auf. Am Ende werden alle Komponenten auf Fehler geprüft.
    def analyze_config(self, mode):
        self.config = mode
        if self.config is None:
            self.errors.append("EdgeOrchestrator found no mode")
            self.logger.error("EdgeOrchestrator found no mode")
            return
        else:
            self.flow = []
            self.flow.append(self.buffer)
            for step in self.config['steps']:
                if step['name'] == 'anonymizer':
                    component = Anonymizer.Anonymizer(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'aggregator_ts':
                    component = Aggregator_Timebased.Aggregator(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'aggregator':
                    component = Aggregator.Aggregator(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'influxdbconnector':
                    component = InfluxDBConnector.InfluxConnector(step['config'])
                    self.flow.append(component)
                elif step['name'] == 'webhookconnector':
                    component = WebhookConnector.WebhookConnector(step['config'])
                    self.flow.append(component)
            for component in self.flow:
                if component.error is not None:
                    self.errors.append(component.error)
                    component.error = None
                if len(self.errors) != 0:
                    self.errors.append("Error in EdgeOrchestrator configuration")

    # method is executed at thread start and only ends when terminate() is called.
    def run(self):
        while not self.terminated:
            self.error_and_info_checker()
            while self.status == "start":
                self.error_and_info_checker()
                self.run_flow()
        self.status = "stop"

    # Methode arbeitet den flow ab und reicht Daten von einer Komponente zur nächsten weiter. Gibt eine Komponente
    # keine Daten zurück, beginnt der flow von vorne. Meldet eine Komponente einen Fehler, wird der flow gestoppt.
    def run_flow(self):
        try:
            self.data = self.flow[self.flow_position].process(self.data)
            if self.data is None or self.flow_position == len(self.flow) - 1:
                self.flow_position = 0
            else:
                self.flow_position += 1
        except Exception as error:
            self.status = "stop"
            self.errors.append("Error in Modul " + str(self.flow[self.flow_position]) + ": " + str(error) + "\nDaten: " + str(self.data))
            self.logger.exception("ERROR:")

    def error_and_info_checker(self):
        for component in self.flow:
            if component.error is not None:
                self.status = "stop"
                self.errors.append(component.error)
                component.error = None
            if component.info is not None:
                self.info.append(component.info)
                self.logger.info(component.info)
                component.info = None




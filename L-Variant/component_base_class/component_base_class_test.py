from component_base_class import ComponentBaseClass
import time
import sys


class ComponentBaseClassTest(ComponentBaseClass):
    def __init__(self):
        super().__init__()
        config_template = {"kafka_broker": "",
                           "source_topic": "",
                           "text": "",
                           "host": ""}
        config = self.get_config(config_template)
        print("Env-Config = ", config)
        print("Text=" + config["text"]["msg"])

        #config = self.get_config(config=config_template, source="file")
        #print("File-Config = ", config)

        self.logger = self.get_logger()

        #self.logger = self.get_logger(logger_type="kafka", kafka_config={"bootstrap_servers": "20.107.220.83:19092",
                                                                        #"topic": "logging_test",
                                                                         #"key": ""})
        self.loop()

    def loop(self):
        elapsed_time = 0
        while not self.terminated:
            time.sleep(5)
            elapsed_time += 5
            print(f"Running for {elapsed_time} seconds.")
            self.logger.debug(f"Running for {elapsed_time} seconds.")
            sys.stdout.flush()
        print("Finished")


if __name__ == '__main__':
    test = ComponentBaseClassTest()





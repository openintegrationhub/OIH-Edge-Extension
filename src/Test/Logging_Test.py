from src.Component.ComponentBaseClass import ComponentBaseClass
import logging

class LoggerTest(ComponentBaseClass):
    def __init__(self, config: dict):
        super().__init__(config)
        self.testel = logging.getLogger("Error-Logger")
        self.testdl = logging.getLogger("Debug-Logger")

    def process(self, data: dict) -> dict:
        print(data["data"])
        self.testel.debug("New Info")
        self.testel.error("New Error")
        return data


if __name__ == '__main__':

    testerrorlogger = logging.getLogger("Error-Logger")
    testdebuglogger = logging.getLogger("Debug-Logger")
    testerrorlogger.setLevel(logging.DEBUG)
    fh1 = logging.FileHandler("testerror.log")
    fh1.setLevel(logging.ERROR)
    testerrorlogger.addHandler(fh1)
    fh2 = logging.FileHandler("testdebug.log")
    fh2.setLevel(logging.DEBUG)
    #testdebuglogger.addHandler(fh2)
    testerrorlogger.addHandler(fh2)

    loggertest = LoggerTest(config={})
    loggertest.process({"data": "Hallo"})
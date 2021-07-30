import datetime

data = {'meta': {'deviceID': 'HQ_Demo_LoRa_CO2_Sensor_Sales_Office'}, 'data': {'Luftfeuchte': [{'timestamp': datetime.datetime(2021, 7, 20, 14, 43, 30), 'value': 46.0}]}}

timestamp = 1545730073

date = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M:%S")

print(date)
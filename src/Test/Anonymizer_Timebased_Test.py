# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 10:56:05 2021

@author: AUS
"""

# Import required packages
import datetime
from src.Component import Anonymizer_Timebased
import random
import time

mode={
    'name':'anonymizer-test',
    'description':'testing the functionality of the anonymizer',
    'steps':[
        {
        'name':'agg',
    'config':{ 
    'default': {"method":'mean',
                "window_size":'5s'},	                            
    'sensor2': {"method":'mean',
                "window_size":'5s'} 
    }
         }
        ]
    }

T_ANN= Anonymizer_Timebased.Anonymizer(mode['steps'][0]['config'])

DATA = {
        'data': {
            'sensor1':[],
            'sensor2':[]
        },
        "meta":{'deviceID':'4711383'}
    }

data_all=[[],[],[]]

START = time.time()
while time.time() - START < 100:
    time.sleep(1)
    
    for _ in range(1):
        #time.sleep(1)
        RANDOM_NUMBER = random.randint(0,100)
        dt=datetime.datetime.now().strftime("%Y-%m-%dT %H:%M:%S:%f")
        DATA['data']['sensor1'].extend([{
            'timestamp': dt,
                 'value': RANDOM_NUMBER}])
        DATA['data']['sensor2'].extend([{
            'timestamp': dt,
                 'value': RANDOM_NUMBER}])

    RET=T_ANN.process(DATA)
    data_all[0].append(DATA['data']['sensor1'][:])
    DATA['data']['sensor1'].clear()
    DATA['data']['sensor2'].clear()
    if RET!=None:
        print(RET)
        data_all[1].append(RET['data']['sensor1'][:])
        data_all[2].append(RET['data']['sensor2'][:])

        